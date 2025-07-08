from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.utils.timezone import now
from django.core.cache import cache
from django.db.models import ExpressionWrapper, F, DateTimeField

from drf_yasg.utils import swagger_auto_schema

from .models import Promotion
from .serializers import PublicPromotionSerializer


    
    

class PublicPromotionListView(ListAPIView):
    serializer_class = PublicPromotionSerializer
    permission_classes = [IsAuthenticated]  # Or IsAuthenticated if needed

    def get_queryset(self):
        return Promotion.objects.annotate(
        end_date_db=ExpressionWrapper(F('start_date') + F('duration'), output_field=DateTimeField())
    ).filter(
        start_date__lte=now(),
        end_date_db__gte=now(),
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
            200: PublicPromotionSerializer,
            404: 'Promotion not found or unavailable.'
        }
    )
    def get(self, request, pk):
        
        cache_key = f"promotion:specific:{pk}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)
        
        prom = Promotion.objects.annotate(
        end_date_db=ExpressionWrapper(F('start_date') + F('duration'), output_field=DateTimeField())
        ).filter(
            pk=pk,
            start_date__lte=now(),
            end_date_db__gte=now(),
            manually_disabled=False
        ).first()
        
        if not prom:
            raise NotFound("Promotion not found or unavailable.")
        
        serializer = PublicPromotionSerializer(prom)
        return Response(serializer.data)
    

    
        