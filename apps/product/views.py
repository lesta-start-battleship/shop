from django.urls import reverse
from django.core.cache import cache
from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from apps.product.models import Product
from apps.product.serializers import ProductSerializer
from apps.saga.saga_orchestrator import start_purchase


class ItemListView(generics.ListAPIView):
	serializer_class = ProductSerializer
	filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
	search_fields = ['name', 'description', 'kind']
	filterset_fields = ['currency_type', 'kind']
	ordering_fields = ['cost', 'name']
	ordering = ['name']

	def get_queryset(self):
		return Product.objects.filter(cost__isnull=False)


class ItemDetailView(generics.RetrieveAPIView):
	serializer_class = ProductSerializer
	lookup_field = 'item_id'
	lookup_url_kwarg = 'item_id'

	def get_queryset(self):
		return Product.objects.filter(cost__isnull=False)

	def retrieve(self, request, *args, **kwargs):
		item_id = kwargs.get("item_id")
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
			Product.objects.filter(cost__isnull=False),
			item_id=item_id
		)

		if not product.check_daily_purchase_limit(user.id):
			return Response(
				{"error": "Превышен дневной лимит для этого предмета"},
				status=status.HTTP_400_BAD_REQUEST
			)
		auth_header = request.headers.get('Authorization', '')
		if not auth_header.startswith('Bearer '):
			return Response(
				{"error": "Токен отсутствует или неверный"},
				status=status.HTTP_401_UNAUTHORIZED
			)
		token = auth_header.split(' ')[1]
		try:
			transaction = start_purchase(
				user_id=user.id,
				item_id=product.item_id,
				cost=product.cost,
				currency_type=product.currency_type,
				promotion_id=product.promotion.id if product.promotion else None,
				token=token
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
			"status_url": request.build_absolute_uri(status_url)
		}, status=status.HTTP_202_ACCEPTED)
