from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductListView, ProductDetailView, AdminProductViewSet, BuyProductView

router = DefaultRouter()
router.register(r'admin/products', AdminProductViewSet, basename='admin-products')

urlpatterns = [
	path('product/', ProductListView.as_view(), name='product-list'),
	path('product/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
	path('product/<int:product_id>/buy/', BuyProductView.as_view(), name='product-buy'),
	# path('<int:id>/buy/', BuyProductView.as_view(), name='product-buy'),
]

urlpatterns += router.urls