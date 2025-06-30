from django.urls import path, include
from apps.promotion import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'promotions', views.PromotionViewSet, basename='promotion')

urlpatterns = router.urls