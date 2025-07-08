import requests
from django.conf import settings
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from rest_framework import viewsets, generics, status
from rest_framework.exceptions import NotFound
from rest_framework.decorators import action
from rest_framework.response import Response

from config.settings import INVENTORY_SERVICE_URL
from .serializers import AdminChestSerializer, AdminProductSerializer, AdminPromotionSerializer
from .utils import get_inventory_headers
from ..chest.models import Chest
from .permissions import IsAdmin
from ..product.models import Product
from ..promotion.models import Promotion
from ..promotion.serializers import PromotionSerializer
from ..promotion.services import compensate_promotion

from drf_yasg.utils import swagger_auto_schema

import logging

logger = logging.getLogger(__name__)


class AdminChestViewSet(viewsets.ModelViewSet):
	queryset = Chest.objects.all()
	serializer_class = AdminChestSerializer
	permission_classes = [IsAdmin]
	lookup_field = 'item_id'
	filter_backends = [DjangoFilterBackend]
	filterset_fields = ['item_id', 'name']

	@swagger_auto_schema(
		operation_summary="List all chests",
		operation_description="Returns a list of all chests in the system. Filter by item_id or name.",
		responses={200: AdminChestSerializer(many=True)}
	)
	def list(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Create a new chest",
		operation_description="Create chest in inventory and save to DB",
		request_body=AdminChestSerializer,
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
			inventory_data = {
				"name": serializer.validated_data['name'],
				"description": f"Сундук: {serializer.validated_data['name']}",
				"script": "chest_reward",
				"use_limit": 0,
				"cooldown": 0,
				"kind": "расходник",
				"shop_item_id": 1,
				"properties": {
					"gold": serializer.validated_data.get('gold', 0),
					"experience": serializer.validated_data.get('experience', 0),
					"reward_distribution": serializer.validated_data.get('reward_distribution', {})
				}
			}
			response = requests.post(
				f"{INVENTORY_SERVICE_URL}/items/create",
				json=inventory_data,
				headers=get_inventory_headers(request),
				timeout=5
			)
			try:
				response_data = response.json()
				item_id = response_data.get('id')

				if item_id:
					serializer.save(item_id=item_id)
					return Response(serializer.data, status=status.HTTP_201_CREATED)

				elif 200 <= response.status_code < 300:
					logger.warning("Inventory service returned success but no item ID")
					return Response(serializer.data, status=status.HTTP_201_CREATED)

				else:
					raise Exception(f"Inventory error: {response.text}")

			except ValueError:
				raise Exception("Invalid inventory service response")

		except Exception as e:
			logger.error(f"Chest creation failed: {str(e)}")
			return Response(
				{"error": str(e)},
				status=status.HTTP_502_BAD_GATEWAY if "Inventory" in str(e)
				else status.HTTP_400_BAD_REQUEST
			)

	@swagger_auto_schema(
		operation_summary="Retrieve a chest",
		operation_description="Get a single chest by item_id.",
		responses={200: AdminChestSerializer()}
	)
	def retrieve(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Update a chest",
		operation_description="Update chest details by item_id.",
		responses={200: AdminChestSerializer()}
	)
	def update(self, request, *args, **kwargs):
		return super().update(request, *args, **kwargs)

	@swagger_auto_schema(
		operation_summary="Delete a chest",
		operation_description="Delete chest from inventory and local DB by item_id",
		responses={
			204: "No content - successfully deleted",
			404: "Chest not found",
			502: "Inventory service error"
		}
	)
	def destroy(self, request, *args, **kwargs):
		try:
			item_id = kwargs.get('item_id')
			chest = Chest.objects.get(item_id=item_id)
			response = requests.delete(
				f"{INVENTORY_SERVICE_URL}/items/{item_id}",
				headers=get_inventory_headers(request),
				timeout=5
			)
			if response.status_code != 204:
				error_msg = f"Inventory error: {response.status_code} - {response.text}"
				logger.error(error_msg)
				raise Exception(error_msg)
			chest.delete()
			return Response(status=status.HTTP_204_NO_CONTENT)

		except Chest.DoesNotExist:
			logger.warning(f"Chest with item_id={item_id} not found")
			return Response(
				{"error": "Chest not found"},
				status=status.HTTP_404_NOT_FOUND
			)
		except Exception as e:
			logger.error(f"Chest deletion failed: {str(e)}")
			return Response(
				{"error": str(e)},
				status=status.HTTP_502_BAD_GATEWAY
			)


class AdminProductListAPIView(generics.ListAPIView):
	queryset = Product.objects.all()
	serializer_class = AdminProductSerializer
	permission_classes = [IsAdmin]
	lookup_field = 'item_id'
	filter_backends = [DjangoFilterBackend]
	filterset_fields = ['item_id', 'name']

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
	lookup_field = 'item_id'

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
