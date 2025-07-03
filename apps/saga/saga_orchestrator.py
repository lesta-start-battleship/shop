# import json
# import logging
# import requests
# import random
# from django.conf import settings
# from apps.saga.models import Transaction
# from config.kafka_config import get_producer
# from kafka.producer import send_chest_promo_purchase_kafka_event
#
# logger = logging.getLogger(__name__)
#
# http_session = requests.Session()
#
#
# def start_purchase(user_id, amount, promotion_id=None, product_id=None, chest_id=None):
# 	try:
# 		if user_id is None:
# 			logger.error("Attempted to start purchase with null user_id")
# 			raise ValueError("user_id cannot be null")
#
# 		transaction = Transaction.objects.create(
# 			user_id=user_id,
# 			product_id=product_id,
# 			chest_id=chest_id,
# 			amount=amount,
# 			promotion_id=promotion_id,
# 			status='PENDING'
# 		)
#
# 		inventory_data = {
# 			'user_id': user_id,
# 			'amount': 1,
# 			'promotion_id': promotion_id
# 		}
# 		if product_id:
# 			inventory_data['item_id'] = product_id
# 		elif chest_id:
# 			inventory_data['chest_id'] = chest_id
# 		auth_command = {
# 			'transaction_id': str(transaction.id),
# 			'user_id': user_id,
# 			'amount': amount,
# 			'promotion_id': promotion_id,
# 			'type': 'withdraw_funds'
# 		}
# 		producer = get_producer()
# 		producer.produce('balance-reserve-commands', json.dumps(auth_command, ensure_ascii=False).encode('utf-8'))
# 		transaction.inventory_data = inventory_data
# 		transaction.save()
# 		producer.flush()
# 		logger.info(f"Started purchase transaction: {transaction.id}")
# 		return transaction
#
# 	except Exception as e:
# 		logger.error(f"Error starting purchase: {str(e)}")
# 		raise
#
#
# def safe_json_parse(message):
# 	if message is None or message.value() is None:
# 		return None
#
# 	try:
# 		return json.loads(message.value().decode('utf-8'))
# 	except json.JSONDecodeError as e:
# 		logger.error(f"JSON decode error: {str(e)}")
# 		return None
# 	except Exception as e:
# 		logger.error(f"Unexpected message parsing error: {str(e)}")
# 		return None
#
#
# def handle_authorization_response(message):
# 	try:
# 		data = safe_json_parse(message)
# 		if not data:
# 			logger.warning("Received empty or invalid auth response message")
# 			return
#
# 		logger.info(f"Received auth response: {data}")
#
# 		try:
# 			transaction = Transaction.objects.get(id=data['transaction_id'])
# 		except (KeyError, ValueError, Transaction.DoesNotExist) as e:
# 			logger.error(f"Invalid transaction data: {str(e)}")
# 			return
#
# 		if data.get('success'):
# 			transaction.status = 'RESERVED'
# 			transaction.save()
# 			logger.info(f"Transaction reserved: {transaction.id}")
#
# 			try:
# 				headers = {
# 					'Authorization': f'Service {settings.SERVICE_SECRET_KEY}',
# 					'Content-Type': 'application/json'
# 				}
# 				if transaction.product_id:
# 					payload = {
# 						'user_id': transaction.user_id,
# 						'item_id': transaction.product_id,
# 						'amount': 1,
# 						'promotion_id': transaction.promotion_id
# 					}
# 				elif transaction.chest_id:
# 					from apps.chest.models import Chest
# 					chest = Chest.objects.get(id=transaction.chest_id)
# 					reward = select_chest_reward(chest)
# 					payload = {
# 						'user_id': transaction.user_id,
# 						'chest_id': transaction.chest_id,
# 						'amount': 1,
# 						'promotion_id': transaction.promotion_id,
# 						'reward': reward
# 					}
#
# 				else:
# 					raise ValueError("Transaction must have either product_id or chest_id")
#
# 				with requests.Session() as http_session:
# 					response = http_session.patch(
# 						f"{settings.INVENTORY_SERVICE_URL}/inventory/add_item",
# 						json=payload,
# 						headers=headers,
# 						timeout=5
# 					)
#
# 				if response.status_code == 200:
# 					transaction.status = 'COMPLETED'
# 					logger.info(f"Transaction completed: {transaction.id}")
# 				else:
# 					raise Exception(f"Inventory error: {response.status_code} - {response.text}")
#
# 			except Exception as e:
# 				logger.error(f"Error calling inventory service: {str(e)}")
# 				transaction.status = 'FAILED'
# 				transaction.error_message = str(e)
# 				initiate_compensation(transaction)
#
# 			transaction.save()
# 		else:
# 			transaction.status = 'DECLINED'
# 			transaction.error_message = data.get('message', 'Authorization failed')
# 			transaction.save()
# 			logger.warning(
# 				f"Authorization failed for transaction: {transaction.id}, reason: {transaction.error_message}")
#
# 	except Exception as e:
# 		logger.error(f"Error handling auth response: {str(e)}")
#
#
#
# def select_chest_reward(chest):
# 	"""Select a reward based on chest's reward_distribution."""
# 	if not chest.reward_distribution:
# 		return None
# 	choices = list(chest.reward_distribution.items())
# 	reward_types = [choice[0] for choice in choices]
# 	probabilities = [choice[1] for choice in choices]
# 	return random.choices(reward_types, weights=probabilities, k=1)[0]
#
#
# def initiate_compensation(transaction):
# 	"""Инициирует компенсационную транзакцию через Kafka"""
# 	compensate_command = {
# 		'transaction_id': str(transaction.id),
# 		'user_id': transaction.user_id,
# 		'amount': transaction.amount,
# 		'promotion_id': transaction.promotion_id,
# 		'type': 'refund_funds',
# 		'reason': transaction.error_message[:255] if transaction.error_message else "Compensation"
# 	}
#
# 	try:
# 		producer = get_producer()
# 		producer.produce(
# 			'balance-compensate-commands',
# 			json.dumps(compensate_command, ensure_ascii=False).encode('utf-8')
# 		)
# 		producer.flush()
#
# 		transaction.status = 'COMPENSATING'
# 		transaction.save()
# 		logger.info(f"Compensation initiated for transaction: {transaction.id}")
# 	except Exception as e:
# 		logger.error(f"Failed to initiate compensation: {str(e)}")
# 		transaction.status = 'COMPENSATION_FAILED'
# 		transaction.error_message = f"Compensation failed: {str(e)}"
# 		transaction.save()
#
#
# def handle_compensation_response(message):
# 	"""Process compensation response from balance service"""
# 	try:
# 		data = safe_json_parse(message)
# 		if not data:
# 			logger.warning("Empty or invalid compensation response")
# 			return
#
# 		logger.info(f"Processing compensation response: {data}")
#
# 		try:
# 			transaction = Transaction.objects.get(id=data['transaction_id'])
# 		except (KeyError, ValueError, Transaction.DoesNotExist) as e:
# 			logger.error(f"Invalid transaction in compensation: {str(e)}")
# 			return
#
# 		if data.get('success'):
# 			transaction.status = 'COMPENSATED'
# 			logger.info(f"Transaction compensated: {transaction.id}")
# 		else:
# 			transaction.status = 'COMPENSATION_FAILED'
# 			transaction.error_message = data.get('message', 'Compensation failed')
# 			logger.error(f"Compensation failed for transaction: {transaction.id}")
#
# 		transaction.save()
#
# 	except Exception as e:
# 		logger.error(f"Error processing compensation: {str(e)}", exc_info=True)
