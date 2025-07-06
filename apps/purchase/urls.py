from django.urls import path
from .views import PurchaseListAPIView

urlpatterns = [
    path('', PurchaseListAPIView.as_view(), name="purchase-list-create"),  # GET /purchase/
]
