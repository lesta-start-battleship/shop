from django.urls import path
from .views import ProductListView, ProductListView, ProductDetailView

urlpatterns = [
	path('product/', ProductListView.as_view(), name='product-list'),
	path('product/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
	# path('<int:id>/buy/', BuyProductView.as_view(), name='product-buy'),
]
