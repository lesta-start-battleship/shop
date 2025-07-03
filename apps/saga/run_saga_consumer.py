# import logging
# from django.core.management.base import BaseCommand
# from apps.saga.saga_orchestrator import (
# 	handle_authorization_response,
# 	handle_compensation_response
# )
#
#
# logger = logging.getLogger(__name__)
#
#
# class Command(BaseCommand):
# 	help = 'Kafka consumer for Saga orchestration'
#
# 	def handle(self, *args, **options):
# 		logger.info("🚀 Starting Saga Orchestrator Consumer...")
#
# 		consumer = None
# 		try:
# 			consumer = get_consumer('saga_orchestrator_group')
#
# 			# Subscribe to both topics
# 			topics = [
# 				'balance-reserve-events',  # Authorization responses
# 				'balance-compensate-events'  # Compensation responses
# 			]
# 			consumer.subscribe(topics)
#
# 			logger.info(f"✅ Subscribed to topics: {', '.join(topics)}")
#
# 			while True:
# 				msg = consumer.poll(1.0)
#
# 				if msg is None:
# 					continue
# 				if msg.error():
# 					logger.error(f"Consumer error: {msg.error()}")
# 					continue
#
# 				# Route message to appropriate handler
# 				if msg.topic() == 'balance-reserve-events':
# 					handle_authorization_response(msg)
# 				elif msg.topic() == 'balance-compensate-events':
# 					handle_compensation_response(msg)
# 				else:
# 					logger.warning(f"Received message from unknown topic: {msg.topic()}")
#
# 		except KeyboardInterrupt:
# 			logger.info("Shutting down consumer...")
# 		except Exception as e:
# 			logger.error(f"Consumer error: {str(e)}", exc_info=True)
# 		finally:
# 			if consumer:
# 				consumer.close()
# 			logger.info("❌ Consumer stopped")
