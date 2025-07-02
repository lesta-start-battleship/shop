from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import time

from apps.saga.models import Transaction
from rest_framework.reverse import reverse


class TransactionStatusView(APIView):
	permission_classes = [IsAuthenticated]

	# Таймаут long-polling в секундах
	POLLING_TIMEOUT = 5

	def get(self, request, *args, **kwargs):
		# Получаем transaction_id из параметров запроса
		transaction_id = request.query_params.get('transaction_id') or kwargs.get('transaction_id')

		if not transaction_id:
			return Response(
				{"error": "transaction_id parameter is required"},
				status=status.HTTP_400_BAD_REQUEST
			)

		try:
			# Проверяем, что транзакция принадлежит текущему пользователю
			transaction = Transaction.objects.get(
				id=transaction_id,
				user_id=request.user.id
			)
		except Transaction.DoesNotExist:
			return Response(
				{"error": "Transaction not found or access denied"},
				status=status.HTTP_404_NOT_FOUND
			)
		except ValueError:
			return Response(
				{"error": "Invalid transaction_id format"},
				status=status.HTTP_400_BAD_REQUEST
			)

		start_time = time.time()

		# Long polling цикл
		while time.time() - start_time < self.POLLING_TIMEOUT:
			# Обновляем данные из БД
			transaction.refresh_from_db()

			# Определяем status_url в зависимости от типа транзакции
			if transaction.chest_id:
				status_url = reverse(
					'chest-buy',  # Assumes URL pattern name for ChestBuyView
					kwargs={'chest_id': transaction.chest_id},
					request=request
				)
			else:
				status_url = reverse(
					'transaction-status',
					kwargs={'transaction_id': str(transaction.id)},
					request=request
				)

			# Если статус изменился (не pending)
			if transaction.status != 'pending':
				return Response({
					"status": transaction.status,
					"error_message": transaction.error_message,
					"data": transaction.inventory_data,
				})

			time.sleep(0.5)  # Ждем перед следующей проверкой

		# Если время ожидания истекло
		return Response({
			"status": transaction.status,
			"message": "Transaction still processing",
			"polling_timeout": True
		})
