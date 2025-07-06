from django.urls import path
from .views import PurchaseListCreateAPIView

urlpatterns = [
    path('', PurchaseListCreateAPIView.as_view(), name="purchase-list-create"),  # GET /purchase/
]
