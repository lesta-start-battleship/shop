from django.contrib.sites import requests
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.product.models import Product
from apps.product.serializers import ProductSerializer


class ProductListView(generics.ListAPIView):
	permission_classes = [IsAuthenticated]
	queryset = Product.objects.all()
	serializer_class = ProductSerializer


class ProductDetailView(generics.RetrieveAPIView):
	permission_classes = [IsAuthenticated]
	queryset = Product.objects.all()
	serializer_class = ProductSerializer
	lookup_field = 'id'


class ProductBuyView(generics.GenericAPIView):
	permission_classes = [IsAuthenticated]
	queryset = Product.objects.all()
	serializer_class = ProductSerializer
	lookup_field = 'id'

	def post(self, request, id):
		try:
			product = self.get_object()
		except Product.DoesNotExist:
			return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
		user_id = request.user.id
		if product.owner != user_id:
			return Response({"error": "You do not own this product"}, status=status.HTTP_403_FORBIDDEN)
		try:
			auth_response = requests.post(
				"http://auth-service/deduct_currency",
				json={"user_id": user_id, "amount": product.cost, "currency_type": "gold"}
			)
			if auth_response.status_code != 200:
				return Response({"error": "Insufficient funds"}, status=status.HTTP_400_BAD_REQUEST)
			inventory_response = requests.post(
				"http://inventory-service/add_item",
				json={"user_id": user_id, "item_id": product.name, "quantity": 1}
			)
			if inventory_response.status_code != 200:
				return Response({"error": "Failed to add to inventory"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

			return Response({"message": f"Successfully bought {product.name}"}, status=status.HTTP_200_OK)

		except Exception as e:
			return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
