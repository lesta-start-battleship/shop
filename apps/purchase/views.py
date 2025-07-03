from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema

from .serializers import PurchaseSerializer
from .models import Purchase
from .services import create_purchase


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

    @swagger_auto_schema(
        operation_description="Создать новую покупку от имени текущего пользователя (заголовок X-User-ID обязателен).",
        request_body=PurchaseSerializer,
        responses={201: PurchaseSerializer, 400: 'Bad Request'}
    )
    def post(self, request):
        user_id = request.user.id
        data = request.data.copy()

        try:
            purchase = create_purchase(
                owner_id=user_id,
                item_id=data.get("item"),
                chest_id=data.get("chest"),
                promotion_id=data.get("promotion"),
                quantity=data.get("quantity", 1),
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PurchaseSerializer(purchase)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
