from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Purchase
from .serializers import PurchaseSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly


@api_view(['GET'])
def list_purchases(request):
    user_id = request.headers.get("X-User-ID")

    if not user_id:
        return Response({"detail": "Unauthorized: missing X-User-ID header"},
                        status=status.HTTP_401_UNAUTHORIZED)

    purchases = Purchase.objects.filter(owner=user_id).order_by('-date')
    serializer = PurchaseSerializer(purchases, many=True)
    return Response(serializer.data)

class PurchaseListCreateAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return Response({"detail": "Missing X-User-ID"}, status=status.HTTP_401_UNAUTHORIZED)

        purchases = Purchase.objects.filter(owner=user_id)
        serializer = PurchaseSerializer(purchases, many=True)
        return Response(serializer.data)

    def post(self, request):
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return Response({"detail": "Missing X-User-ID"}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()
        data["owner"] = user_id
        serializer = PurchaseSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
