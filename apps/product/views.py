from django.urls import reverse
from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.product.models import Product
from apps.product.serializers import ProductSerializer
from apps.saga.saga_orchestrator import start_purchase


class ItemListView(generics.ListAPIView):
	serializer_class = ProductSerializer

	def get_queryset(self):
		return Product.objects.filter(
			cost__isnull=False
		)
  
	def list(self, request, *args, **kwargs):
			cache_key = "product:public:active"
			cached_data = cache.get(cache_key)

			if cached_data:
				return Response(cached_data)

			queryset = self.get_queryset().order_by("id")
			serializer = self.get_serializer(queryset, many=True)
			cache.set(cache_key, serializer.data, timeout=60 * 5) 

			return Response(serializer.data)


class ItemDetailView(generics.RetrieveAPIView):
	serializer_class = ProductSerializer

	def get_queryset(self):
		return Product.objects.filter(
			cost__isnull=False
		)
  
	def retrieve(self, request, *args, **kwargs):
			item_id = kwargs.get("pk")
			cache_key = f"product:detail:{item_id}"

			cached_data = cache.get(cache_key)
			if cached_data:
				return Response(cached_data)

			
			response = super().retrieve(request, *args, **kwargs)

			
			cache.set(cache_key, response.data, timeout=60 * 10)

			return response



class ItemBuyView(APIView):
	def post(self, request, item_id):
		user = request.user

		if not user.id:
			return Response(
				{"error": "ID пользователя отсутствует или неверный"},
				status=status.HTTP_400_BAD_REQUEST
			)

		product = get_object_or_404(
			Product.objects.filter(
				cost__isnull=False
			),
			id=item_id
		)

		# Проверка индивидуального лимита только если предмет не в акции
		if not product.check_daily_purchase_limit(user.id):
			return Response(
				{"error": "Превышен дневной лимит для этого предмета"},
				status=status.HTTP_400_BAD_REQUEST
			)

		try:
			transaction = start_purchase(
				user_id=user.id,
				product_id=product.id,
				cost=product.cost,
				currency_type=product.currency_type,
				promotion_id=product.promotion.id if product.promotion else None
			)
		except Exception as e:
			return Response(
				{"error": str(e)},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)

		status_url = reverse(
			'transaction-status',
			kwargs={'transaction_id': str(transaction.id)},
		)

		return Response({
			"status": "purchase_started",
			"transaction_id": str(transaction.id),
			"status_url": status_url
		}, status=status.HTTP_202_ACCEPTED)
