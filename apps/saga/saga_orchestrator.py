import json
import logging
import requests
import random
from django.core.cache import cache

from config.settings import KAFKA_BOOTSTRAP_SERVERS, INVENTORY_SERVICE_URL
from .models import Transaction
from apps.promotion.external import InventoryService
from confluent_kafka import Producer
from apps.purchase.services import create_purchase

from prometheus_metrics import (
	gold_spent_total,
	successful_purchases_total,
	failed_purchases_total,
	successful_promo_purchases_total,
)
from ..chest.models import Chest


def safe_json_decode(msg):
	try:
		return json.loads(msg.value().decode('utf-8'))
	except Exception as e:
		logger.error(f"[Kafka] JSON decode error: {e}")
		return None


def get_producer():
	return Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})


logger = logging.getLogger(__name__)


def start_purchase(user_id, cost, currency_type, promotion_id=None, item_id=None, token=None):
	try:
		if user_id is None:
			raise ValueError("user_id cannot be null")
		if token is None:
			raise ValueError("token cannot be null")

		transaction = Transaction.objects.create(
			user_id=user_id,
			item_id=item_id,
			cost=cost,
			currency_type=currency_type,
			promotion_id=promotion_id,
			status='PENDING'
		)

		cache.set(f"transaction:{transaction.id}:token", token, timeout=300)

		inventory_data = {
			'user_id': user_id,
			'amount': 1,
			'promotion_id': promotion_id,
			'currency_type': currency_type,
			'item_id': item_id
		}

		auth_command = {
			'transaction_id': str(transaction.id),
			'user_id': user_id,
			'cost': cost,
			'currency_type': currency_type,
		}

		producer = get_producer()
		producer.produce(
			'shop.balance.reserve.request.auth',
			json.dumps(auth_command, ensure_ascii=False).encode('utf-8')
		)
		producer.flush()

		transaction.inventory_data = inventory_data
		transaction.save()

		logger.info(f"Started purchase transaction: {transaction.id}")
		return transaction

	except Exception as e:
		logger.error(f"Error starting purchase: {str(e)}")
		raise


def handle_authorization_response(message):
	try:
		data = safe_json_decode(message)
		if not data:
			logger.warning("Received empty or invalid auth response message")
			return

		logger.info(f"Received auth response: {data}")

		try:
			transaction = Transaction.objects.get(id=data['transaction_id'])
		except (KeyError, ValueError, Transaction.DoesNotExist) as e:
			logger.error(f"Invalid transaction data: {str(e)}")
			return

		if data.get('success') is True:
			transaction.status = 'RESERVED'
			transaction.save()
			logger.info(f"Transaction reserved: {transaction.id}")

			try:
				user_token = cache.get(f"transaction:{transaction.id}:token")
				if not user_token:
					raise ValueError("Token not found in transaction")

				headers = {
					'Authorization': f'Bearer {user_token}',
					'Content-Type': 'application/json'
				}

				if not transaction.item_id:
					raise ValueError("Transaction must have item_id")

				payload = {
					'item_id': transaction.item_id,
					'amount': 1
				}
				logger.info(f"Transaction started. Token {user_token}")
				with requests.Session() as http_session:
					response = http_session.patch(
						f"{INVENTORY_SERVICE_URL}/inventory/add_item",
						json=payload,
						headers=headers,
						timeout=5
					)
				logger.info(response)	
				if response.status_code == 200:
					transaction.status = 'COMPLETED'
					logger.info(f"Transaction completed: {transaction.id}")
					purchase = create_purchase(
						owner_id=transaction.user_id,
						item_id=transaction.item_id,
						promotion_id=transaction.promotion_id,
						quantity=1
					)
					gold_spent_total.inc(transaction.cost)
					successful_purchases_total.inc()
					if transaction.promotion_id is not None:
						successful_promo_purchases_total.inc()

					logger.info(f"✅ Purchase created after successful transaction {purchase}")
				else:
					raise Exception(f"Inventory error: {response.status_code} - {response.text}")

			except Exception as e:
				logger.error(f"Error calling inventory service: {str(e)}")
				transaction.status = 'FAILED'
				failed_purchases_total.inc()
				transaction.error_message = str(e)
				initiate_compensation(transaction)

			transaction.save()
		else:
			error_code = data.get('error_message')
			transaction.status = 'FAILED'
			transaction.error_message = error_code,
			transaction.save()

			logger.warning(
				f"Authorization failed for transaction {transaction.id}. "
				f"Reason: {transaction.error_message}. "
				f"Error code: {error_code}"
			)

	except Exception as e:
		logger.error(f"Error handling auth response: {str(e)}")



def initiate_compensation(transaction):
	compensate_command = {
		'transaction_id': str(transaction.id),
		'user_id': transaction.user_id,
		'cost': transaction.cost,
		'currency_type': transaction.currency_type
	}

	try:
		producer = get_producer()
		producer.produce(
			'shop.balance.compensate.request.auth',
			json.dumps(compensate_command, ensure_ascii=False).encode('utf-8')
		)
		producer.flush()

		transaction.status = 'COMPENSATING'
		transaction.save()
		logger.info(f"Compensation initiated for transaction: {transaction.id}")
	except Exception as e:
		logger.error(f"Failed to initiate compensation: {str(e)}")
		transaction.status = 'COMPENSATION_FAILED'
		transaction.error_message = f"Compensation failed: {str(e)}"
		transaction.save()


def handle_compensation_response(message):
	try:
		data = safe_json_decode(message)
		if not data:
			logger.warning("Empty or invalid compensation response")
			return

		logger.info(f"Processing compensation response: {data}")

		try:
			transaction = Transaction.objects.get(id=data['transaction_id'])
		except (KeyError, ValueError, Transaction.DoesNotExist) as e:
			logger.error(f"Invalid transaction in compensation: {str(e)}")
			return

		if data.get('success') is True:
			transaction.status = 'COMPENSATED'
			logger.info(f"Transaction compensated: {transaction.id}")
		else:
			transaction.status = 'COMPENSATION_FAILED'
			transaction.error_message = data.get('message', 'Compensation failed')
			logger.error(f"Compensation failed for transaction: {transaction.id}")

		transaction.save()

	except Exception as e:
		logger.error(f"Error processing compensation: {str(e)}", exc_info=True)


def publish_promotion_compensation(user_id: int, amount: int, item_id: int, role=None, currency="gold"):
	event = {
		"user_id": user_id,
		"amount": amount,
		"currency": currency,
		"item_id": item_id,
	}

	if role:
		event["role"] = role

	try:
		producer = get_producer()
		producer.produce(
			'promotion.compensation.commands',
			json.dumps(event, ensure_ascii=False).encode('utf-8')
		)
		producer.flush()
		logger.info(f"Compensation event sent for user {user_id}, amount {amount} {currency}")
	except Exception as e:
		logger.error(f"Failed to publish compensation event: {str(e)}")


def handle_promotion_compensation_response(message):
	try:
		data = safe_json_decode(message)
		if not data:
			logger.warning("Invalid compensation response")
			return

		success = data.get("success")
		user_id = data.get("user_id")
		item_id = data.get("item_id")

		if success:
			InventoryService.delete_item(item_id)
			logger.info(f"Deleted item {item_id} after successful compensation for user {user_id}")
		else:
			logger.error(f"Compensation failed for user {user_id}, item {item_id}, reason: {data.get('message')}")

	except Exception as e:
		logger.error(f"Error processing compensation response: {str(e)}", exc_info=True)
