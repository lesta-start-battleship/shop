import time

from django.urls import reverse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Product
from .serializers import ProductSerializer, ProductPurchaseSerializer
from apps.saga.models import SagaOrchestrator



class ProductListView(generics.ListAPIView):
	serializer_class = ProductSerializer

	def get_queryset(self):
		return Product.objects.filter(
			cost__isnull=False,
			chest__isnull=True
		).select_related('promotion')


class ProductPurchaseView(generics.CreateAPIView):
	permission_classes = [IsAuthenticated]
	serializer_class = ProductPurchaseSerializer

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			product = Product.objects.get(pk=serializer.validated_data['product_id'])

			# Проверка доступности товара
			if product.cost is None:
				return Response(
					{"detail": "Product cost is not set"},
					status=status.HTTP_400_BAD_REQUEST
				)

			if product.chest is not None:
				return Response(
					{"detail": "Cannot purchase product in chest directly"},
					status=status.HTTP_400_BAD_REQUEST
				)

			# Создаем транзакцию
			saga = SagaOrchestrator(
				user_id=request.user.id,
				product_type='product',
				product_id=product.id,
				quantity=serializer.validated_data['quantity'],
				currency_type=product.currency_type,
				promotion=product.promotion,
				events=[]
			)

			# Запускаем транзакцию
			if not saga.start_transaction():
				return Response(
					{
						"detail": "Failed to start transaction",
						"error": saga.error_reason
					},
					status=status.HTTP_400_BAD_REQUEST
				)

			# Генерируем URL для проверки статуса
			status_url = f"{reverse('transaction-status')}?transaction_id={saga.transaction_id}"

			# Формируем текстовое сообщение для JSON
			message = (
				f"Транзакция создана. ID: {saga.transaction_id}\n"
				f"Статус: {saga.status}\n"
				f"Для проверки статуса: {status_url}"
			)

			# Возвращаем JSON-ответ
			return Response(
				{"message": message},
				status=status.HTTP_201_CREATED
			)

		except Product.DoesNotExist:
			return Response(
				{"detail": "Product not found"},
				status=status.HTTP_404_NOT_FOUND
			)
		except Exception as e:
			return Response(
				{"detail": "Internal server error"},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)


class TransactionStatusView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		transaction_id = request.GET.get('transaction_id')
		if not transaction_id:
			return Response({"error": "transaction_id is required"}, status=400)

		try:
			# Проверяем, что транзакция принадлежит текущему пользователю
			saga = SagaOrchestrator.objects.get(transaction_id=transaction_id, user_id=request.user.id)
		except SagaOrchestrator.DoesNotExist:
			return Response({"error": "Transaction not found"}, status=404)

		start_time = time.time()
		timeout = 10  # Уменьшенное время ожидания в секундах

		# Цикл long polling
		while time.time() - start_time < timeout:
			# Проверяем, не истек ли тайм-аут транзакции
			if saga.check_timeout():
				return Response({"status": saga.status, "error_reason": saga.error_reason})

			if saga.status != 'processing':
				# Если статус изменился, возвращаем его
				return Response({"status": saga.status, "error_reason": saga.error_reason})

			time.sleep(1)  # Ждем 1 секунду перед следующей проверкой
			saga.refresh_from_db()  # Обновляем данные из базы

		# Если время ожидания истекло
		return Response({"status": "processing", "message": "Still processing"})


