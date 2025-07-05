from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import time

from apps.saga.models import Transaction
from rest_framework.reverse import reverse


class TransactionStatusView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request, *args, **kwargs):
		transaction_id = request.query_params.get('transaction_id') or kwargs.get('transaction_id')

		if not transaction_id:
			return Response(
				{"error": "transaction_id parameter is required"},
				status=status.HTTP_400_BAD_REQUEST
			)

		try:
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

		return Response({
			"status": transaction.status,
			"error_message": transaction.error_message,
			"data": transaction.inventory_data,
		})
