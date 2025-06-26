from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Purchase
from .serializers import PurchaseSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_purchases(request):
    """
    Возвращает список покупок текущего пользователя, полученного из JWT-токена.
    """
    user_id = request.user.id  # Получаем из токена
    purchases = Purchase.objects.filter(owner=user_id).order_by('-date')
    serializer = PurchaseSerializer(purchases, many=True)
    return Response(serializer.data)
