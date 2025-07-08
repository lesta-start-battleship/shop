from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib import admin

schema_view = get_schema_view(
	openapi.Info(
		title="Shop Service API",
		default_version='v1',
		description="API documentation for Shop service (promotions, products, purchases)",
		terms_of_service="https://example.com/terms/",
		contact=openapi.Contact(email="support@example.com"),
		license=openapi.License(name="BSD License"),
	),
	public=True,
	permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
	# path('admin/', include('apps.custom_admin.urls')),
	path('admin/', admin.site.urls),
	path('item/', include('apps.product.urls')),
	path('promotion/', include('apps.promotion.urls')),
	path('purchase/', include('apps.purchase.urls')),
	path('chest/', include('apps.chest.urls')),
	path('transaction/', include('apps.saga.urls')),
	# Swagger and Redoc endpoints
	re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
	path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
	path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

	# Prometheus
	path('', include('django_prometheus.urls')),  # добавляет /metrics
]
