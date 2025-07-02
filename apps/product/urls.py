from django.urls import path
from .views import ProductListView, ProductPurchaseView, TransactionStatusView

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('purchase/', ProductPurchaseView.as_view(), name='product-purchase'),
    path('transactions/long-poll/', TransactionStatusView.as_view(), name='transaction-status')
]