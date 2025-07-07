import json
import logging
import requests
import random
from django.conf import settings
from .models import Transaction
from apps.promotion.external import InventoryService
from confluent_kafka import Producer
from apps.purchase.services import create_purchase

from prometheus_metrics import (
	gold_spent_total,
	successful_purchases_total,
	failed_purchases_total,
	successful_chest_purchases_total,
	successful_product_purchases_total,
	successful_promo_purchases_total,
)


def safe_json_decode(msg):
	try:
		return json.loads(msg.value().decode('utf-8'))
	except Exception as e:
		logger.error(f"[Kafka] JSON decode error: {e}")
		return None


def get_producer():
	return Producer({'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS})


logger = logging.getLogger(__name__)

http_session = requests.Session()


def start_purchase(user_id, cost, currency_type, promotion_id=None, product_id=None, chest_id=None):
	try:
		if user_id is None:
			logger.error("Attempted to start purchase with null user_id")
			raise ValueError("user_id cannot be null")

		transaction = Transaction.objects.create(
			user_id=user_id,
			product_id=product_id,
			chest_id=chest_id,
			cost=cost,
			currency_type=currency_type,
			promotion_id=promotion_id,
			status='PENDING'
		)

		inventory_data = {
			'user_id': user_id,
			'amount': 1,
			'promotion_id': promotion_id,
			'currency_type': currency_type
		}
		if product_id:
			inventory_data['item_id'] = product_id
		elif chest_id:
			inventory_data['chest_id'] = chest_id

		auth_command = {
			'transaction_id': str(transaction.id),
			'user_id': user_id,
			'cost': cost,
			'currency_type': currency_type
		}

		producer = get_producer()
		producer.produce('shop.balance.reserve.request.auth', json.dumps(auth_command, ensure_ascii=False).encode('utf-8'))
		transaction.inventory_data = inventory_data
		transaction.save()
		producer.flush()
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
				headers = {
					'Authorization': f'Service {settings.SERVICE_SECRET_KEY}',
					'Content-Type': 'application/json'
				}
				if transaction.product_id:
					payload = {
						'user_id': transaction.user_id,
						'item_id': transaction.product_id,
						'amount': 1,
						'promotion_id': transaction.promotion_id,
						'currency_type': transaction.currency_type
					}
				elif transaction.chest_id:
					from apps.chest.models import Chest
					chest = Chest.objects.get(id=transaction.chest_id)
					reward = select_chest_reward(chest)
					payload = {
						'user_id': transaction.user_id,
						'chest_id': transaction.chest_id,
						'amount': 1,
						'promotion_id': transaction.promotion_id,
						'reward': reward,
						'currency_type': transaction.currency_type  # Added
					}

				else:
					raise ValueError("Transaction must have either product_id or chest_id")

				with requests.Session() as http_session:
					response = http_session.patch(
						f"{settings.INVENTORY_SERVICE_URL}/inventory/add_item",
						json=payload,
						headers=headers,
						timeout=5
					)

				if response.status_code == 200:
					transaction.status = 'COMPLETED'
					logger.info(f"Transaction completed: {transaction.id}")
					purchase = create_purchase(
						owner_id=transaction.user_id,
						item_id=transaction.product_id,
						chest_id=transaction.chest_id,
						promotion_id=transaction.promotion_id,
						quantity=1
					)
					# Метрики
					gold_spent_total.inc(transaction.cost)
					successful_purchases_total.inc()

					if transaction.chest_id:
						successful_chest_purchases_total.inc()
					if transaction.product_id:
						successful_product_purchases_total.inc()
					if transaction.promotion_id is not None:
						successful_promo_purchases_total.inc()
					logger.info(f"✅ Purchase created after successful transaction: {purchase}")
				else:
					raise Exception(f"Inventory error: {response.status_code} - {response.text}")

			except Exception as e:
				logger.error(f"Error calling inventory service: {str(e)}")
				transaction.status = 'FAILED'
				transaction.error_message = str(e)
				initiate_compensation(transaction)

			transaction.save()
		else:
			error_code = data.get('code', 'authorization_failed')
			default_message = 'Authorization failed'

			error_messages = {
				'insufficient_funds': 'Not enough money in account',
				'invalid_credentials': 'Invalid payment credentials',
				'limit_exceeded': 'Daily spending limit exceeded',
				'authorization_failed': default_message
			}

			transaction.status = 'DECLINED'
			transaction.error_message = data.get(
				'message',
				error_messages.get(error_code, default_message)
			)
			transaction.save()

			logger.warning(
				f"Authorization failed for transaction {transaction.id}. "
				f"Reason: {transaction.error_message}. "
				f"Error code: {error_code}"
			)

	except Exception as e:
		logger.error(f"Error handling auth response: {str(e)}")


def select_chest_reward(chest):
	"""Select a reward based on chest's reward_distribution."""
	if not chest.reward_distribution:
		return None
	choices = list(chest.reward_distribution.items())
	reward_types = [choice[0] for choice in choices]
	probabilities = [choice[1] for choice in choices]
	return random.choices(reward_types, weights=probabilities, k=1)[0]


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
