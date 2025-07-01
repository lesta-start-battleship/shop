from django.conf.urls.static import static, settings
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('product/', include('apps.product.urls')),
    path('promotion/', include('apps.promotion.urls')),
    path('purchase/', include('apps.purchase.urls')),
    path('chest/', include('apps.chest.urls')),
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
