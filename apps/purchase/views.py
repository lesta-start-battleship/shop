from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Purchase
from .serializers import PurchaseSerializer


@api_view(["GET"])
def list_purchases(request):
	uid = request.query_params.get("user_id")
	if not uid:
		return Response({"error": "user_id обязателен"}, status=400)
	purchases = Purchase.objects.filter(owner=uid).order_by("-date")
	return Response(PurchaseSerializer(purchases, many=True).data)
