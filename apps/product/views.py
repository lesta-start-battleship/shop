from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.product.models import Product
from apps.product.serializers import ProductSerializer


class ProductListView(APIView):
	def get(self, request):
		products = Product.objects.filter(chest__isnull=True)
		serializer = ProductSerializer(products, many=True)
		return Response(serializer.data)


class ProductDetailView(APIView):
	def get(self, request, pk):
		try:
			product = Product.objects.get(pk=pk, chest__isnull=True)
		except Product.DoesNotExist:
			return Response({"detail": "Product not found or inside chest"}, status=status.HTTP_404_NOT_FOUND)
		serializer = ProductSerializer(product)
		return Response(serializer.data)

# AUTH_SERVICE_RESERVE_URL = "http://auth-service/api/auth/reserve/"
# AUTH_SERVICE_COMMIT_URL = "http://auth-service/api/auth/commit/"
# INVENTORY_SERVICE_ADD_ITEM_URL = "http://inventory-service/api/inventory/add-item/"
#
#
# class BuyProductView(APIView):
# 	# Используем настройки из settings.py: JWTAuthentication + IsAuthenticated
#
# 	def post(self, request, product_id):
# 		user = request.user  # {'user_id': ..., 'username': ..., ...}
#
# 		try:
# 			product = Product.objects.get(pk=product_id)
# 		except Product.DoesNotExist:
# 			return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
#
# 		transaction_id = str(uuid.uuid4())
#
# 		# Шаг 1: Резервируем средства в auth-сервисе
# 		reserve_payload = {
# 			"user_id": user.get("user_id"),
# 			"transaction_id": transaction_id,
# 			"cost": product.price
# 		}
# 		reserve_res = requests.post(
# 			AUTH_SERVICE_RESERVE_URL,
# 			json=reserve_payload,
# 			timeout=5
# 		)
# 		if reserve_res.status_code != status.HTTP_200_OK:
# 			return Response({"detail": "Failed to reserve funds"}, status=status.HTTP_502_BAD_GATEWAY)
#
# 		# Шаг 2: Добавляем товар в инвентарь
# 		inventory_payload = {
# 			"user_id": user.get("user_id"),
# 			"product_id": product.id,
# 			"transaction_id": transaction_id
# 		}
# 		inventory_res = requests.post(
# 			INVENTORY_SERVICE_ADD_ITEM_URL,
# 			json=inventory_payload,
# 			timeout=5
# 		)
#
# 		if inventory_res.status_code != status.HTTP_200_OK:
# 			return Response({"detail": "Failed to add item to inventory"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
# 		# Шаг 3: Подтверждаем резерв, списываем баланс
# 		commit_payload = {"transaction_id": transaction_id}
# 		commit_res = requests.post(
# 			AUTH_SERVICE_COMMIT_URL,
# 			json=commit_payload,
# 			timeout=5
# 		)
#
# 		if commit_res.status_code != status.HTTP_200_OK:
# 			return Response({"detail": "Failed to finalize balance commit"}, status=status.HTTP_502_BAD_GATEWAY)
#
# 		return Response({
# 			"detail": "Product purchased and added to inventory",
# 			"transaction_id": transaction_id
# 		}, status=status.HTTP_200_OK)
