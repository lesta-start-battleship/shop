from django.urls import path
from .views import *


urlpatterns = [
	path('', ProductListView.as_view(), name='item-list'),
	path('<int:item_id>/', ProductDetailView.as_view(), name='item-detail'),
	path('<int:item_id>/buy/', ProductBuyView.as_view(), name='item-buy'),
]
