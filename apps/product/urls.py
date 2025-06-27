from django.urls import path
from .views import ProductListView, ProductDetailView, ProductBuyView

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('<int:id>/', ProductDetailView.as_view(), name='product-detail'),
    path('<int:id>/buy/', ProductBuyView.as_view(), name='product-buy'),
]