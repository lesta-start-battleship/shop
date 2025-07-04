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
from .services import compensate_promotion
from .models import Promotion
from .serializers import PromotionSerializer

class PromotionViewSet(ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAdminUser]
    
    
    @swagger_auto_schema(operation_description="Compensate unopened chests for this promotion.")
    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def compensate(self, request):
        promotion = self.get_object()
        try:
            count = compensate_promotion(promotion)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        return Response({"detail": f"Compensated {count} items."})

class PublicPromotionListView(ListAPIView):
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticated]  # Or IsAuthenticated if needed

    def get_queryset(self):
        # Only show active promotions to users
        return Promotion.objects.filter(
            start_date__lte=now(),
            end_date__gte=now(),
            manually_disabled=False
        )

class SpecificPromotionView(APIView):
    @swagger_auto_schema(
        operation_summary="Get Specific Promotion",
        operation_description="Returns details of a specific active promotion by its ID. "
                              "If the promotion has ended, is inactive, or does not exist, returns 404.",
        responses={
            200: PromotionSerializer,
            404: 'Promotion not found or unavailable.'
        }
    )
    def get(self, request, pk):
        
        prom = Promotion.objects.filter(
            pk=pk,
            start_date__lte=now(),
            end_date__gte=now(),
            manually_disabled=False
        ).first()
        
        if not prom:
            raise NotFound("Promotion not found or unavailable.")
        
        serializer = PromotionSerializer(prom)
        return Response(serializer.data)
    

    
        