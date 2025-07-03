
from django.urls import path, include
from apps.promotion import views
from rest_framework.routers import DefaultRouter

from apps.promotion.views import PromotionViewSet

router = DefaultRouter()
router.register(r'', PromotionViewSet, basename='promotion')

urlpatterns = [
    path('', include(router.urls)),
    path('', views.PublicPromotionListView.as_view()),
    path('<int:pk>/', views.SpecificPromotionView.as_view()),
    path('<int:pk>/buy', views.BuyPromotionView.as_view()),
]