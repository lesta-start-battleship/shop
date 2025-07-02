from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.reverse import reverse
from .models import Chest
from .serializers import ChestSerializer
from apps.saga.saga_orchestrator import start_purchase


class ChestListView(generics.ListAPIView):
	queryset = Chest.objects.all()
	serializer_class = ChestSerializer


class ChestDetailView(generics.RetrieveAPIView):
	queryset = Chest.objects.all()
	serializer_class = ChestSerializer





class ChestBuyView(APIView):
	def post(self, request, chest_id):
		user = request.user
		chest = get_object_or_404(Chest, id=chest_id)

		# Проверка лимитов акции
		if chest.promotion and not chest.promotion.check_user_limit(user.id):
			return Response({"error": "Promotion limit exceeded"}, status=status.HTTP_400_BAD_REQUEST)

		# Запуск саги покупки
		try:
			transaction = start_purchase(
				user_id=user.id,
				chest_id=chest.id,
				amount=chest.cost,
				promotion_id=chest.promotion.id if chest.promotion else None
			)
		except Exception as e:
			return Response(
				{"error": str(e)},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)

		# Generate status_url for transaction status endpoint
		status_url = reverse(
			'transaction-status',
			kwargs={'transaction_id': str(transaction.id)},
			request=request
		)

		return Response({
			"status": "purchase_started",
			"transaction_id": str(transaction.id),
			"status_url": status_url
		}, status=status.HTTP_202_ACCEPTED)
