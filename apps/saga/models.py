import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.db import transaction
from confluent_kafka import Producer, KafkaException
import json
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from apps.chest.models import Chest
from apps.product.models import Product


class SagaOrchestrator(models.Model):
	STATUS_CHOICES = [
		('processing', 'Processing'),
		('completed', 'Completed'),
		('failed', 'Failed'),
		('compensating', 'Compensating'),
		('compensated', 'Compensated'),
	]

	PRODUCT_TYPE_CHOICES = [
		('product', 'Product'),
		('chest', 'Chest'),
	]

	STEP_CHOICES = [
		('started', 'Started'),
		('balance_reserve_requested', 'Balance Reserve Requested'),
		('balance_reserved', 'Balance Reserved'),
		('inventory_update_requested', 'Inventory Update Requested'),
		('inventory_updated', 'Inventory Updated'),
		('promotion_limits_updated', 'Promotion Limits Updated'),
		('compensating_balance', 'Compensating Balance'),
	]

	# Основные поля транзакции
	transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user_id = models.IntegerField(validators=[MinValueValidator(1)])
	product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
	product_id = models.IntegerField(validators=[MinValueValidator(1)])
	quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
	amount = models.IntegerField(validators=[MinValueValidator(1)])
	currency_type = models.CharField(max_length=32)
	promotion = models.ForeignKey(
		'promotion.Promotion',
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="saga_transactions"
	)

	# Состояние и отслеживание
	current_step = models.CharField(max_length=50, choices=STEP_CHOICES, default='started')
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
	error_reason = models.TextField(null=True, blank=True)
	events = models.JSONField(default=list, blank=True)  # Разрешаем пустой список

	# Таймауты
	timeout_at = models.DateTimeField(null=True, blank=True)

	# Временные метки
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		indexes = [
			models.Index(fields=['status', 'timeout_at']),
			models.Index(fields=['user_id']),
		]

	def __str__(self):
		return f"{self.transaction_id} - {self.status}"

	def clean(self):
		"""Валидация перед сохранением"""
		# Проверка положительной суммы
		if self.amount <= 0:
			raise ValidationError("Amount must be positive")

		# Установка таймаута
		if not self.timeout_at and self.status == 'processing':
			self.timeout_at = timezone.now() + timedelta(minutes=30)

	def save(self, *args, **kwargs):
		"""Переопределение save с валидацией"""
		self.clean()

		# Гарантируем, что events всегда является списком
		if not isinstance(self.events, list):
			self.events = []

		super().save(*args, **kwargs)

	def add_event(self, event_name, payload=None):
		"""Добавление события в историю"""
		if not isinstance(self.events, list):
			self.events = []

		event = {
			'name': event_name,
			'timestamp': timezone.now().isoformat(),
			'payload': payload or {}
		}
		self.events.append(event)

		# Сохраняем только измененные поля
		update_fields = ['events', 'updated_at']
		if not self.pk:  # Если объект новый, сохраняем все поля
			super().save(update_fields=update_fields)
		else:
			super().save(update_fields=update_fields)

	def start_transaction(self):
		"""Запуск транзакции с проверкой состояния"""
		try:
			# Проверка состояния
			if self.status != 'processing' or self.current_step != 'started':
				self.add_event('invalid_start_state', {
					'current_status': self.status,
					'current_step': self.current_step
				})
				return False

			# Получаем продукт/сундук
			if self.product_type == 'product':
				product = Product.objects.get(id=self.product_id)
				if product.chest is not None:
					raise ValidationError("Cannot purchase product in chest directly")
				if product.cost is None:
					raise ValidationError("Product cost is not set")
				self.currency_type = product.currency_type
				self.amount = product.cost * self.quantity

				if product.promotion:
					self.promotion = product.promotion
					self.amount = int(product.promotion.price * self.quantity)

			elif self.product_type == 'chest':
				chest = Chest.objects.get(id=self.product_id)
				if chest.cost is None:
					raise ValidationError("Chest cost is not set")
				self.currency_type = chest.currency_type
				self.amount = chest.cost * self.quantity

				if chest.promotion:
					self.promotion = chest.promotion
					self.amount = int(chest.promotion.price * self.quantity)

			# Сохраняем рассчитанные значения
			self.save()

			self.add_event('transaction_started')
			self._send_balance_command()

			# Обновляем состояние
			self.current_step = 'balance_reserve_requested'
			self.save(update_fields=['current_step', 'updated_at'])

			return True

		except Exception as e:
			self._handle_transaction_error(str(e))
			return False

	# Остальные методы остаются без изменений (_send_kafka_command, _send_balance_command и т.д.)
	# ... (копируем остальные методы из вашего предыдущего кода)
	def _send_kafka_command(self, topic, message):
		"""Общий метод отправки команд в Kafka"""
		try:
			producer = Producer({'bootstrap.servers': '37.9.53.228:9092'})
			producer.produce(
				topic=topic,
				value=json.dumps(message).encode('utf-8'),
				key=str(self.transaction_id)
			)
			producer.flush()
			self.add_event(f'{topic}_sent', message)
		except KafkaException as e:
			self._handle_transaction_error(f"Kafka error: {str(e)}")
			raise

	def _send_balance_command(self):
		"""Отправка команды резервирования"""
		self._send_kafka_command(
			topic='balance-reserve-commands',
			message={
				'transaction_id': str(self.transaction_id),
				'user_id': self.user_id,
				'amount': self.amount,
				'currency_type': self.currency_type
			}
		)

	def handle_balance_response(self, success, response_data):
		"""Обработка ответа от баланс-сервиса"""
		with transaction.atomic():
			self.add_event('balance_response', {
				'success': success,
				'data': response_data
			})

			if success:
				self._send_inventory_command()
				self.current_step = 'inventory_update_requested'
			else:
				self.status = 'failed'
				self.error_reason = response_data.get('reason', 'Balance reserve failed')

			self.save()

	def _send_inventory_command(self):
		"""Отправка команды обновления инвентаря"""
		self._send_kafka_command(
			topic='inventory-update-commands',
			message={
				'transaction_id': str(self.transaction_id),
				'user_id': self.user_id,
				'product_type': self.product_type,
				'product_id': self.product_id,
				'quantity': self.quantity,
				'is_promotional': bool(self.promotion)
			}
		)

	def handle_inventory_response(self, success, response_data):
		"""Обработка ответа от инвентаря"""
		with transaction.atomic():
			self.add_event('inventory_response', {
				'success': success,
				'data': response_data
			})

			if success:
				if self.promotion:
					self._update_promotion_limits()
				self._complete_transaction()
			else:
				self._start_compensation()

			self.save()

	def _update_promotion_limits(self):
		"""Обновление лимитов акции"""
		try:
			self.promotion.used_count += self.quantity
			self.promotion.save()
			self.add_event('promotion_updated')
		except Exception as e:
			self.add_event('promotion_update_error', {'error': str(e)})

	def _complete_transaction(self):
		"""Завершение успешной транзакции"""
		self.status = 'completed'
		self.current_step = 'inventory_updated'
		self._send_kafka_command(
			topic='balance-complete-commands',
			message={
				'transaction_id': str(self.transaction_id),
				'status': 'completed'
			}
		)

	def _start_compensation(self):
		"""Инициализация компенсации"""
		self.status = 'compensating'
		self.current_step = 'compensating_balance'
		self._send_kafka_command(
			topic='balance-compensate-commands',
			message={
				'transaction_id': str(self.transaction_id),
				'user_id': self.user_id,
				'amount': self.amount,
				'currency_type': self.currency_type
			}
		)

	def handle_compensation_response(self, success, response_data):
		"""Обработка ответа на компенсацию"""
		with transaction.atomic():
			self.add_event('compensation_response', {
				'success': success,
				'data': response_data
			})

			self.status = 'compensated' if success else 'failed'
			if not success:
				self.error_reason = f"Compensation failed: {response_data.get('reason', 'Unknown error')}"

			self.save()

	def check_timeout(self):
		"""Проверка таймаута транзакции"""
		if self.status == 'processing' and self.timeout_at and timezone.now() > self.timeout_at:
			with transaction.atomic():
				self.status = 'failed'
				self.error_reason = "Transaction timed out"
				self.save()
				self._notify_client(success=False)
			return True
		return False

	def _notify_client(self, success):
		"""Заглушка для уведомления клиента"""
		self.add_event('client_notified', {'success': success})

	def _handle_transaction_error(self, error_msg):
		"""Обработка ошибок транзакции"""
		self.status = 'failed'
		self.error_reason = error_msg
		self.save()
		self._notify_client(success=False)
