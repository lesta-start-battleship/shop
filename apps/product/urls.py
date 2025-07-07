from django.urls import path
from .views import *


urlpatterns = [
	path('', ItemListView.as_view(), name='item-list'),
	path('<int:item_id>/', ItemDetailView.as_view(), name='item-detail'),
	path('<int:item_id>/buy/', ItemBuyView.as_view(), name='item-buy'),
]
