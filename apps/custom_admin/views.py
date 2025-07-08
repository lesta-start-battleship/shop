from drf_yasg import openapi
from rest_framework import viewsets, generics, status
from rest_framework.exceptions import NotFound
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import AdminChestSerializer, AdminProductSerializer, AdminPromotionSerializer
from ..chest.models import Chest
from .permissions import IsAdmin
from ..product.models import Product
from ..promotion.models import Promotion
from ..promotion.serializers import PromotionSerializer
from ..promotion.services import compensate_promotion

from drf_yasg.utils import swagger_auto_schema

from .utils import create_inventory_item, delete_inventory_item


class AdminChestViewSet(viewsets.ModelViewSet):
	queryset = Chest.objects.all()
	serializer_class = AdminChestSerializer
	permission_classes = [IsAdmin]

	@swagger_auto_schema(
		operation_summary="List all chests",
		operation_description="Returns a list of all chests in the system.",
		responses={200: AdminChestSerializer(many=True)}
	)
	def list(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Create a new chest",
		operation_description="Create and return a new chest.",
		responses={
			201: AdminChestSerializer(),
			400: "Bad Request",
			502: "Inventory Service Error"
		}
	)
	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			item_id = create_inventory_item(request, serializer.validated_data)
			if not item_id:
				raise ValueError("Inventory service didn't return item ID")
			serializer.save(item_id=item_id)

			headers = self.get_success_headers(serializer.data)
			return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

		except Exception as e:
			return Response(
				{"error": str(e)},
				status=status.HTTP_502_BAD_GATEWAY if "Inventory service" in str(e)
				else status.HTTP_401_UNAUTHORIZED if "credentials" in str(e)
				else status.HTTP_400_BAD_REQUEST
			)

	@swagger_auto_schema(
		operation_summary="Retrieve a chest",
		operation_description="Get a single chest by ID.",
		responses={200: AdminChestSerializer()}
	)
	def retrieve(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Update a chest",
		operation_description="Update chest details by ID.",
		responses={200: AdminChestSerializer()}
	)
	def update(self, request, *args, **kwargs):
		return super().update(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Delete a chest",
		operation_description="Delete chest by ID.",
		responses={204: openapi.Response(description='No content')}
	)
	def destroy(self, request, *args, **kwargs):
		instance = self.get_object()
		item_id = instance.item_id

		try:
			delete_inventory_item(request, item_id)
			self.perform_destroy(instance)
			return Response(status=status.HTTP_204_NO_CONTENT)

		except Exception as e:
			return Response(
				{"error": str(e)},
				status=status.HTTP_502_BAD_GATEWAY
			)


class AdminProductListAPIView(generics.ListAPIView):
	permission_classes = [IsAdmin]
	serializer_class = AdminProductSerializer
	queryset = Product.objects.all()

	@swagger_auto_schema(
		operation_summary="List all products",
		operation_description="Returns a list of all products available in the system.",
		responses={200: AdminProductSerializer(many=True)}
	)
	def get(self, request, *args, **kwargs):
		return super().get(request, *args, **kwargs)


class AdminProductAPIView(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = [IsAdmin]
	serializer_class = AdminProductSerializer
	queryset = Product.objects.all()
	lookup_field = 'pk'

	def get_object(self):
		try:
			return super().get_object()
		except Product.DoesNotExist:
			raise NotFound("Product not found")

	@swagger_auto_schema(
		operation_summary="Retrieve a product",
		operation_description="Get a single product by its ID.",
		responses={200: AdminProductSerializer()}
	)
	def get(self, request, *args, **kwargs):
		return super().get(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Update a product",
		operation_description="Update product details by ID.",
		responses={200: AdminProductSerializer()}
	)
	def put(self, request, *args, **kwargs):
		return super().put(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Delete a product",
		operation_description="Delete product by ID.",
		responses={204: 'No content'}
	)
	def delete(self, request, *args, **kwargs):
		return super().delete(request, *args, **kwargs)


class AdminPromotionViewSet(viewsets.ModelViewSet):
	queryset = Promotion.objects.all()
	serializer_class = AdminPromotionSerializer

	permission_classes = [IsAdmin]

	@swagger_auto_schema(
		operation_summary="List all promotions",
		operation_description="Returns a list of all promotions available in the system.",
		responses={200: PromotionSerializer(many=True)}
	)
	def list(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Retrieve a promotion",
		operation_description="Returns detailed information about a specific promotion by its ID.",
		responses={200: PromotionSerializer}
	)
	def retrieve(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Create a new promotion",
		operation_description="Creates a new promotion with the specified parameters.",
		responses={201: PromotionSerializer}
	)
	def create(self, request, *args, **kwargs):
		return super().create(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Update a promotion",
		operation_description="Updates the details of an existing promotion.",
		responses={200: PromotionSerializer}
	)
	def update(self, request, *args, **kwargs):
		return super().update(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Delete a promotion",
		operation_description="Deletes a promotion by its ID.",
		responses={204: "No Content",
				   400: "Cannot delete an active promotion. Wait until it ends"}
	)
	def destroy(self, request, *args, **kwargs):
		promo = self.get_object()
		if not promo.has_ended():
			return Response(
				{"detail": "Cannot delete an active promotion. Wait until it ends"},
				status=status.HTTP_400_BAD_REQUEST
			)
		return super().destroy(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Compensate unopened chests",
		operation_description="Compensates unopened chests and unused items for this promotion. Can only be triggered if promotion has ended.",
		responses={
			200: "Compensation completed successfully.",
			400: "Promotion is still active or already compensated."
		}
	)
	@action(detail=True, methods=["post"], permission_classes=[IsAdmin])
	def compensate(self, request, pk=None):
		promotion = self.get_object()
		try:
			count = compensate_promotion(promotion)
		except ValueError as e:
			return Response({"detail": str(e)}, status=400)

		return Response({"detail": f"Compensated {count} items."})
