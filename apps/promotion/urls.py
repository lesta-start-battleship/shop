from django.urls import path, include
import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'promotions', views.PromotionViewSet, basename='promotion')

urlpatterns = [
    path('', include(router.urls)),
    path('', views.PublicPromotionListView.as_view()),
    path('<int:pk>/', views.SpecificPromotionView.as_view()),
]