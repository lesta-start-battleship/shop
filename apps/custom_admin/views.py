from rest_framework import viewsets, generics
from rest_framework.exceptions import NotFound


from .serializers import AdminChestSerializer, AdminProductSerializer, AdminPromotionSerializer
from ..chest.models import Chest
from .permissions import IsAdmin
from ..product.models import Product
from ..promotion.models import Promotion


class AdminChestViewSet(viewsets.ModelViewSet):
	queryset = Chest.objects.all()
	serializer_class = AdminChestSerializer
	permission_classes = [IsAdmin]


class AdminProductListAPIView(generics.ListAPIView):
	permission_classes = [IsAdmin]
	serializer_class = AdminProductSerializer
	queryset = Product.objects.all()


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


class AdminPromotionViewSet(viewsets.ModelViewSet):
	queryset = Promotion.objects.all()
	serializer_class = AdminPromotionSerializer
	permission_classes = [IsAdmin]
