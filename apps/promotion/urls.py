
from django.urls import path
from apps.promotion import views

urlpatterns = [
    path('', views.PublicPromotionListView.as_view()),
    path('<int:pk>/', views.SpecificPromotionView.as_view()),
]