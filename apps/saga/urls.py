from django.urls import path
from .views import TransactionStatusView

urlpatterns = [
	path('<uuid:transaction_id>/', TransactionStatusView.as_view(), name='transaction-status'),
]