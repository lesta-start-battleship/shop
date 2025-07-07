from django.urls import path
from .views import *

urlpatterns = [
	path('', ChestListView.as_view(), name='chest-list'),
	path('<int:pk>/', ChestDetailView.as_view(), name='chest-detail'),
	path('<int:chest_id>/buy/', ChestBuyView.as_view(), name='chest-buy'),
	path('open/', OpenChestView.as_view(), name='chest-open'),
]
