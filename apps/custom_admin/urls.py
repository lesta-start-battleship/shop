from django.urls import path, include

from .views import AdminChestViewSet, AdminProductAPIView, AdminPromotionViewSet, AdminProductListAPIView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register('chest', AdminChestViewSet, basename='chest-admin')
router.register('promotion', AdminPromotionViewSet, basename='promotion-admin')

urlpatterns = [
	path('', include(router.urls)),
	path('products/', AdminProductListAPIView.as_view(), name='admin-product-list'),
	path('products/<int:pk>/', AdminProductAPIView.as_view(), name='admin-product-detail'),
]
