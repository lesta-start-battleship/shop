from django.urls import path, include

from .views import AdminChestViewSet, AdminProductAPIView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register('chest', AdminChestViewSet, basename='chest-admin')



urlpatterns = [
	path('', include(router.urls)),
	path('products/', AdminProductAPIView.as_view(), name='admin-product'),
	path('products/<int:pk>/', AdminProductAPIView.as_view(), name='admin-product')
]
