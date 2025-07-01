from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from .models import Purchase
from .serializers import PurchaseSerializer


@swagger_auto_schema(
    method='get',
    operation_description="Get list of purchases for current user (X-User-ID header required).",
    responses={200: PurchaseSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_purchases(request):
    purchases = Purchase.objects.filter(owner=request.user.id).order_by('-date')
    serializer = PurchaseSerializer(purchases, many=True)
    return Response(serializer.data)


class PurchaseListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get list of purchases for current user (X-User-ID header required).",
        responses={200: PurchaseSerializer(many=True)}
    )
    def get(self, request):
        purchases = Purchase.objects.filter(owner=request.user.id)
        serializer = PurchaseSerializer(purchases, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new purchase for current user (X-User-ID header required).",
        request_body=PurchaseSerializer,
        responses={
            201: PurchaseSerializer,
            400: 'Bad Request'
        }
    )
    def post(self, request):
        data = request.data.copy()
        data["owner"] = request.user.id
        serializer = PurchaseSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def get_user_id_from_request(request) -> int:
    """
    Извлекает user_id из request.user, предполагая, что используется XUserIDAuthentication.
    """
    if not request.user or request.user.is_anonymous:
        raise ValueError("Anonymous user")

    return request.user.id