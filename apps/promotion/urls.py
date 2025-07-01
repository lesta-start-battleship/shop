
from rest_framework.routers import DefaultRouter

from apps.promotion.views import PromotionViewSet

router = DefaultRouter()
router.register(r'promotions', PromotionViewSet, basename='promotion')

urlpatterns = router.urls
