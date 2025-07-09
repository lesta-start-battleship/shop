import json
import logging
import requests
from django.core.cache import cache
from django.db import transaction
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

		inventory_data = {
			'user_id': user_id,
			'amount': 1,
			'promotion_id': promotion_id,
			'currency_type': currency_type,
			'item_id': item_id
		}

		txn = Transaction.objects.create(
			user_id=user_id,
			item_id=item_id,
			cost=cost,
			currency_type=currency_type,
			promotion_id=promotion_id,
			status='PENDING',
			inventory_data=inventory_data
		)

		cache.set(f"transaction:{txn.id}:token", token, timeout=30)

		auth_command = {
			'transaction_id': str(txn.id),
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

		txn.inventory_data = inventory_data
		txn.save()

		logger.info(f"Started purchase transaction: {txn.id}")
		return txn

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
			with transaction.atomic():
				txn = Transaction.objects.select_for_update().get(id=data['transaction_id'])
				if txn.status != 'PENDING':
					logger.warning(f"Transaction {txn.id} is not in PENDING state")
					return
		except (KeyError, ValueError, Transaction.DoesNotExist) as e:
			logger.error(f"Invalid transaction data: {str(e)}")
			return

		if data.get('success') is True:
			txn.status = 'RESERVED'
			txn.save()
			logger.info(f"Transaction reserved: {txn.id}")

			try:
				user_token = cache.get(f"transaction:{txn.id}:token")
				if not user_token:
					raise ValueError("Token not found in transaction")

				headers = {
					'Authorization': f'Bearer {user_token}',
					'Content-Type': 'application/json'
				}

				if not txn.item_id:
					raise ValueError("Transaction must have item_id")

				payload = {
					'item_id': txn.item_id,
					'amount': 1,
				}
				with requests.Session() as http_session:
					response = http_session.patch(
						f"{INVENTORY_SERVICE_URL}/inventory/add_item",
						json=payload,
						headers=headers,
						timeout=5
					)
				logger.info(response)
				if response.status_code == 200:
					txn.status = 'COMPLETED'
					logger.info(f"Transaction completed: {txn.id}")
					purchase = create_purchase(
						owner_id=txn.user_id,
						item_id=txn.item_id,
						promotion_id=txn.promotion_id,
						quantity=1
					)
					gold_spent_total.inc(txn.cost)
					successful_purchases_total.inc()
					if txn.promotion_id is not None:
						successful_promo_purchases_total.inc()
					logger.info(f"✅ Purchase created: {purchase}")
				else:
					raise Exception(f"Inventory error: {response.status_code} - {response.text}")

			except Exception as e:
				logger.error(f"Error calling inventory service: {str(e)}")
				txn.status = 'FAILED'
				failed_purchases_total.inc()
				txn.error_message = str(e)
				initiate_compensation(txn)

			txn.save()
		else:
			error_code = data.get('error_message')
			txn.status = 'FAILED'
			txn.error_message = error_code
			txn.save()
			logger.warning(f"Authorization failed: {txn.id}. Reason: {error_code}")

	except Exception as e:
		logger.error(f"Error handling auth response: {str(e)}")


def initiate_compensation(txn):
	compensate_command = {
		'transaction_id': str(txn.id),
		'user_id': txn.user_id,
		'cost': txn.cost,
		'currency_type': txn.currency_type
	}

	try:
		producer = get_producer()
		producer.produce(
			'shop.balance.compensate.request.auth',
			json.dumps(compensate_command, ensure_ascii=False).encode('utf-8')
		)
		producer.flush()

		txn.status = 'COMPENSATING'
		txn.save()
		logger.info(f"Compensation initiated for transaction: {txn.id}")
	except Exception as e:
		logger.error(f"Failed to initiate compensation: {str(e)}")
		txn.status = 'COMPENSATION_FAILED'
		txn.error_message = f"Compensation failed: {str(e)}"
		txn.save()


def handle_compensation_response(message):
	try:
		data = safe_json_decode(message)
		if not data:
			logger.warning("Empty or invalid compensation response")
			return

		logger.info(f"Processing compensation response: {data}")

		try:
			txn = Transaction.objects.get(id=data['transaction_id'])
		except (KeyError, ValueError, Transaction.DoesNotExist) as e:
			logger.error(f"Invalid transaction in compensation: {str(e)}")
			return

		if data.get('success') is True:
			txn.status = 'COMPENSATED'
			logger.info(f"Transaction compensated: {txn.id}")
		else:
			txn.status = 'COMPENSATION_FAILED'
			txn.error_message = data.get('message', 'Compensation failed')
			logger.error(f"Compensation failed for transaction: {txn.id}")

		txn.save()

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
