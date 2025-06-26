from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Purchase
from .apps import PurchaseSerializer

@api_view(["GET"])
def purchase_list(request):
    """
    Таблица покупок для Scoreboard / Инвентаря
    """
    purchases = Purchase.objects.all()
    return Response(PurchaseSerializer(purchases, many=True).data)
