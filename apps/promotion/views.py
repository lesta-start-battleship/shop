from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework import status
from django.utils.timezone import now
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from .services import compensate_promotion
from .models import Promotion
from .serializers import PromotionSerializer

class PromotionViewSet(ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAdminUser]
    
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
    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def compensate(self, request, pk=None):
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
        return Promotion.objects.filter(
            start_date__lte=now(),
            end_date__gte=now(),
            manually_disabled=False
        )

    def list(self, request, *args, **kwargs):
        cache_key = "promotion:public:active"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        cache.set(cache_key, serializer.data, timeout=60 * 5)  # Cache for 5 minutes

        return Response(serializer.data)

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
        
        cache_key = f"promotion:specific:{pk}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)
        
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
    

    
        