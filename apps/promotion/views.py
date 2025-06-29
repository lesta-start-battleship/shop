from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action 
from rest_framework import status
from rest_framework.responses import Response
from drf_yasg.utils import swagger_auto_schema
from .services import compensate_unopened_chests, promotion_has_ended

from .models import Promotion
from .serializers import PromotionSerializer


class PromotionViewSet(ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAdminUser]
    
    
    @swagger_auto_schema(operation_description="Compensate unopened chests for this promotion.")
    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def compensate(self, request, pk=None):
        promotion = self.get_object()
        
        if not promotion_has_ended(promotion):
            return Response({"detail": "Promotion still active."}, status=400)
        compensated = compensate_unopened_chests(promotion)
        
        return Response({"detail": f"Compensated {compensated} unopened chests."})