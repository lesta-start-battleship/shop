from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.product.models import Product
from apps.product.serializers import ProductSerializer
from apps.purchase.services import start_product_purchase
from apps.purchase.serializers import PurchaseSerializer
from apps.purchase.views import get_user_id_from_request


class ProductListView(APIView):
    @swagger_auto_schema(operation_description="Get list of all products (excluding those inside chests)")
    def get(self, request):
        products = Product.objects.filter(chest__isnull=True)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    @swagger_auto_schema(operation_description="Get details of a product by ID (excluding those inside chests)")
    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk, chest__isnull=True)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found or inside chest"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product)
        return Response(serializer.data)


class AdminProductViewSet(viewsets.ModelViewSet):
    """
    Admin CRUD for Product: create, update, delete products.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(operation_description="Get list of all products")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Create a new product")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Update product by ID")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Delete product by ID")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class BuyProductView(APIView):
    user_id_header = openapi.Parameter(
        "X-User-ID",
        openapi.IN_HEADER,
        description="User ID from API Gateway",
        type=openapi.TYPE_INTEGER,
        required=True,
    )

    @swagger_auto_schema(
        operation_description="Purchase a product by ID",
        manual_parameters=[user_id_header],
        responses={201: PurchaseSerializer}
    )
    def post(self, request, product_id):
        user_id, error = get_user_id_from_request(request)
        if error:
            return error

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        if not product.cost:
            return Response({"detail": "Product has no cost"}, status=status.HTTP_400_BAD_REQUEST)

        purchase = start_product_purchase(user_id, product_id)
        return Response(PurchaseSerializer(purchase).data, status=status.HTTP_201_CREATED)
