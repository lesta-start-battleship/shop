# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
import time
from .models import SagaOrchestrator


class TransactionStatusView(APIView):
	"""
	Long Polling endpoint для проверки статуса транзакции.
	Держит соединение открытым до изменения статуса или таймаута.
	"""

	def get(self, request):
		transaction_id = request.query_params.get('transaction_id')
		timeout = int(request.query_params.get('timeout', 30))  # Таймаут по умолчанию 30 сек

		if not transaction_id:
			return HttpResponseBadRequest("Transaction ID is required")

		try:
			saga = get_object_or_404(SagaOrchestrator, transaction_id=transaction_id)

			# Если статус уже финальный, возвращаем сразу
			if saga.status not in ['processing', 'compensating']:
				return Response(saga.get_status_data())

			# Long Polling цикл
			start_time = time.time()
			check_interval = 0.5  # Проверяем каждые 0.5 секунды

			while time.time() - start_time < timeout:
				saga.refresh_from_db()
				if saga.status not in ['processing', 'compensating']:
					return Response(saga.get_status_data())
				time.sleep(check_interval)

			# Если таймаут истек
			return Response({
				"transaction_id": transaction_id,
				"status": "timeout",
				"message": "Long polling timeout reached",
				"current_status": saga.status
			}, status=status.HTTP_200_OK)

		except Exception as e:
			return Response(
				{"error": str(e)},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
