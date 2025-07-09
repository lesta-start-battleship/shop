from django.urls import path
from .views import *

urlpatterns = [
	path('', ChestListView.as_view(), name='chest-list'),
	path('<int:item_id>/', ChestDetailView.as_view(), name='chest-detail'),
	path('<int:item_id>/buy/', ChestBuyView.as_view(), name='chest-buy'),
	path('open/', OpenChestView.as_view(), name='chest-open'),
	path('chest_settings/', ChestSettingsView.as_view(), name='chest-settings'),
]
