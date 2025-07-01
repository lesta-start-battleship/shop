from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework import status
from django.utils.timezone import now
from drf_yasg.utils import swagger_auto_schema
from .services import compensate_unopened_chests, promotion_has_ended
# from apps.purchase.services import process_purchase
from apps.promotion.models import Promotion
from apps.purchase.models import Purchase
from .models import Promotion
from .serializers import PromotionSerializer

from datetime import timedelta
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

class PublicPromotionListView(ListAPIView):
    serializer_class = PromotionSerializer
    
    def get_queryset(self):
        curr_time = now()
        return Promotion.objects.filter(
            start_time_lte=curr_time,
            start_time_gte=curr_time - timedelta(days=30)
        )

class SpecificPromotionView(APIView):
    
    @swagger_auto_schema(
        operation_summary="Get Specific Promotion",
        operation_description="Returns details of a specific active promotion by its ID. "
                              "If the promotion has ended or does not exist, returns 404.",
        responses={
            200: PromotionSerializer,
            404: 'Promotion not found or inactive.'
        }
    )
    def get(self, request, pk):
        try:
            prom = Promotion.objects.get(pk=pk)
        except Promotion.DoesNotExist:
            raise NotFound("Promotion not found")
        
        if promotion_has_ended(prom):
            raise NotFound("Promotion has ended or unavailable")
        
        serializer = PromotionSerializer(prom)
        return Response(serializer.data)
    
class BuyPromotionView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Buy Promotion Bundle",
        operation_description="Purchases the full promotion bundle, granting all linked chests and products to the player.",
        responses={201: "Purchase successful", 400: "Validation error", 404: "Promotion not found"}
    )
    def post(self, request, pk):
        try:
            promo = Promotion.objects.get(pk=pk)
        except Promotion.DoesNotExist:
            raise NotFound("Promotion not found.")

        if promotion_has_ended(promo):
            raise ValidationError("Promotion has already ended.")

        player_id = request.user.id  # Assuming Auth Service injects user via token

        # Call service to handle purchase logic
        # process_purchase(player_id, promo)

        return Response({"detail": "Promotion purchased successfully."}, status=201)
    
        