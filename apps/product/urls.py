from django.urls import path
from .views import *


urlpatterns = [
	path('item/', ItemListView.as_view(), name='item-list'),
	path('item/<int:pk>/', ItemDetailView.as_view(), name='item-detail'),
	path('item/<int:item_id>/buy/', ItemBuyView.as_view(), name='item-buy'),
]
