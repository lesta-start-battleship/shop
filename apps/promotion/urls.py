from django.urls import path, include
from apps.promotion.views import PromotionViewSet


urlpatterns = [
    path('', PromotionViewSet.as_view({'post': 'compensate'})),
]
