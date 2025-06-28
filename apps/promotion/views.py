from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action 
from rest_framework import status
from .services import compensate_unopened_chests

from .models import Promotion
from .serializers import PromotionSerializer

# Create your views here.
class PromotionViewSet(ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def compensate(self, request, pk=None):
        pass