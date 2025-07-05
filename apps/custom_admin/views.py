from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AdminChestSerializer, AdminProductSerializer
from ..chest.models import Chest
from .permissions import IsAdmin
from ..product.models import Product


class AdminChestViewSet(viewsets.ModelViewSet):
	queryset = Chest.objects.all()
	serializer_class = AdminChestSerializer
	permission_classes = [IsAdmin]


class AdminProductAPIView(APIView):
	permission_classes = [IsAdmin]

	def get_object(self, pk):
		try:
			return Product.objects.get(pk=pk)
		except Product.DoesNotExist:
			raise NotFound("Product not found")

	def get(self, request, pk):
		product = self.get_object(pk)
		serializer = AdminProductSerializer(product)
		return Response(serializer.data)

	def put(self, request, pk):
		product = self.get_object(pk)
		serializer = AdminProductSerializer(product, data=request.data, partial=False, context={"request": request})
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def patch(self, request, pk):
		product = self.get_object(pk)
		serializer = AdminProductSerializer(product, data=request.data, partial=True, context={"request": request})
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
