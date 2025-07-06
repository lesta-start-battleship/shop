from pathlib import Path
import environ, sys, os

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="very-secret-key")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

INVENTORY_SERVICE_URL = env("INVENTORY_SERVICE_URL", default="http://localhost")
AUTH_SERVICE_URL = env("AUTH_SERVICE_URL", default="http://localhost")
SERVICE_SECRET_KEY = env("SERVICE_SECRET_KEY", default="your-secret-key-for-inter-service-auth")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'django_celery_beat',

	'rest_framework',
	'corsheaders',
	'django_prometheus',
	'drf_yasg',

	'apps.product.apps.ProductConfig',
	'apps.promotion.apps.PromotionConfig',
	'apps.chest.apps.ChestConfig',
	'apps.purchase.apps.PurchaseConfig',
	'apps.saga.apps.SagaConfig',
	'apps.custom_admin.apps.CustomAdminConfig',
]

MIDDLEWARE = [
	'django_prometheus.middleware.PrometheusBeforeMiddleware',
	'django.middleware.security.SecurityMiddleware',
	'whitenoise.middleware.WhiteNoiseMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'corsheaders.middleware.CorsMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
	'django_prometheus.middleware.PrometheusAfterMiddleware',
]

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [BASE_DIR / 'templates'],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
			],
		},
	},
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql',
		'NAME': env('POSTGRES_DB', default='postgres'),
		'USER': env('POSTGRES_USER', default='postgres'),
		'PASSWORD': env('POSTGRES_PASSWORD', default='postgres'),
		'HOST': env('POSTGRES_HOST', default='localhost'),
		'PORT': env('POSTGRES_PORT', default='5432'),
	}
}

CACHES = {
	"default": {
		"BACKEND": "django_redis.cache.RedisCache",
		"LOCATION": f"redis://{env('REDIS_HOST', default='redis')}:{env('REDIS_PORT', default='6379')}/1",
		"OPTIONS": {
			"CLIENT_CLASS": "django_redis.client.DefaultClient",
		}
	}
}

CELERY_BROKER_URL = f"redis://{env('REDIS_HOST', default='redis')}:{env('REDIS_PORT', default='6379')}/0"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': {
		'verbose': {
			'format': '[{asctime}] {levelname} [{name}] {message}',
			'style': '{',
		},
		'simple': {
			'format': '{levelname}: {message}',
			'style': '{',
		},
	},
	'handlers': {
		'console': {
			'class': 'logging.StreamHandler',
			'stream': sys.stdout,
			'formatter': 'verbose',
		},
	},
	'root': {
		'handlers': ['console'],
		'level': 'DEBUG' if DEBUG else 'INFO',
	},
	'loggers': {
		'django': {
			'handlers': ['console'],
			'level': 'DEBUG' if DEBUG else 'INFO',
			'propagate': False,
		},
		'apps.kafka': {
			'handlers': ['console'],
			'level': 'DEBUG',
			'propagate': False,
		},
	},
}

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

REST_FRAMEWORK = {
	'DEFAULT_AUTHENTICATION_CLASSES': [
		# 'rest_framework_simplejwt.authentication.JWTAuthentication',
		'config.authentication.GatewayJWTAuthentication',

	],
	'DEFAULT_PERMISSION_CLASSES': [
		'rest_framework.permissions.IsAuthenticated',
	],
	'DEFAULT_THROTTLE_RATES': {
		'anon': '50/min',
		'user': '50/min'
	}
}

CORS_ALLOW_ALL_ORIGINS = DEBUG
ROOT_URLCONF = 'config.urls'

SWAGGER_SETTINGS = {
	'SECURITY_DEFINITIONS': {
		'Bearer': {
			'type': 'apiKey',
			'name': 'Authorization',
			'in': 'header',
			'description': 'Введите JWT токен в формате: Bearer <токен>'
		}
	},
	'USE_SESSION_AUTH': False,  # отключить login/logout в Swagger
}
