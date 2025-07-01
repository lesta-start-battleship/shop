from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from .models import Purchase
from .serializers import PurchaseSerializer

def get_user_id_from_request(request):
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return None, Response({"detail": "Missing X-User-ID header"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        user_id_int = int(user_id)
    except ValueError:
        return None, Response({"detail": "Invalid X-User-ID header"}, status=status.HTTP_400_BAD_REQUEST)
    return user_id_int, None


@swagger_auto_schema(
    method='get',
    operation_description="Get list of purchases for current user (X-User-ID header required).",
    responses={200: PurchaseSerializer(many=True)}
)
@api_view(['GET'])
def list_purchases(request):
    user_id, error_response = get_user_id_from_request(request)
    if error_response:
        return error_response

    purchases = Purchase.objects.filter(owner=user_id).order_by('-date')
    serializer = PurchaseSerializer(purchases, many=True)
    return Response(serializer.data)


class PurchaseListCreateAPIView(APIView):

    @swagger_auto_schema(
        operation_description="Get list of purchases for current user (X-User-ID header required).",
        responses={200: PurchaseSerializer(many=True)}
    )
    def get(self, request):
        user_id, error_response = get_user_id_from_request(request)
        if error_response:
            return error_response

        purchases = Purchase.objects.filter(owner=user_id)
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
        user_id, error_response = get_user_id_from_request(request)
        if error_response:
            return error_response

        data = request.data.copy()
        data["owner"] = user_id
        serializer = PurchaseSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
