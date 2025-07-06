from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from drf_yasg.utils import swagger_auto_schema

from .serializers import PurchaseSerializer
from .models import Purchase


class PurchaseListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получить список покупок текущего пользователя (заголовок X-User-ID обязателен).",
        responses={200: PurchaseSerializer(many=True)}
    )
    def get(self, request):
        purchases = Purchase.objects.filter(owner=request.user.id).order_by('-date')
        serializer = PurchaseSerializer(purchases, many=True)
        return Response(serializer.data)
