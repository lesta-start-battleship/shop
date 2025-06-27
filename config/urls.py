from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('product/', include('apps.product.urls')),
    path('promotion/', include('apps.promotion.urls')),
    path('purchase/', include('apps.purchase.urls')),
    path('chest/', include('apps.chest.urls')),
]
