from django.urls import path
from .views import TransactionStatusView

urlpatterns = [
	path('transaction/<uuid:transaction_id>/', TransactionStatusView.as_view(), name='transaction-status'),
]