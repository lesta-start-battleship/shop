# from django.urls import reverse
# from rest_framework import generics, status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from django.shortcuts import get_object_or_404
#
# from apps.product.models import Product
# from apps.product.serializers import ProductSerializer
# from apps.saga.saga_orchestrator import start_purchase
#
#
# class ItemListView(generics.ListAPIView):
# 	serializer_class = ProductSerializer
#
# 	def get_queryset(self):
# 		return Product.objects.filter(
# 			chest__isnull=True,
# 			cost__isnull=False
# 		)
#
#
# class ItemDetailView(generics.RetrieveAPIView):
# 	serializer_class = ProductSerializer
#
# 	def get_queryset(self):
# 		return Product.objects.filter(
# 			chest__isnull=True,
# 			cost__isnull=False
# 		)
#
#
# class ItemBuyView(APIView):
# 	permission_classes = [IsAuthenticated]
#
# 	def post(self, request, item_id):
# 		user = request.user
#
# 		if not user.id:
# 			return Response(
# 				{"error": "ID пользователя отсутствует или неверный"},
# 				status=status.HTTP_400_BAD_REQUEST
# 			)
#
# 		product = get_object_or_404(
# 			Product.objects.filter(
# 				chest__isnull=True,
# 				cost__isnull=False
# 			),
# 			id=item_id
# 		)
#
# 		# Проверка индивидуального лимита только если предмет не в акции
# 		if not product.check_daily_purchase_limit(user.id):
# 			return Response(
# 				{"error": "Превышен дневной лимит для этого предмета"},
# 				status=status.HTTP_400_BAD_REQUEST
# 			)
#
# 		try:
# 			transaction = start_purchase(
# 				user_id=user.id,
# 				product_id=product.id,
# 				amount=product.cost,
# 				promotion_id=product.promotion.id if product.promotion else None
# 			)
# 		except Exception as e:
# 			return Response(
# 				{"error": str(e)},
# 				status=status.HTTP_500_INTERNAL_SERVER_ERROR
# 			)
#
# 		status_url = reverse(
# 			'transaction-status',
# 			kwargs={'transaction_id': str(transaction.id)},
# 		)
#
# 		return Response({
# 			"status": "purchase_started",
# 			"transaction_id": str(transaction.id),
# 			"status_url": status_url
# 		}, status=status.HTTP_202_ACCEPTED)
