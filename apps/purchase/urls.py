from django.urls import path
from .views import list_purchases

urlpatterns = [
    path('', list_purchases),  # GET /purchase/?user_id=123
]
