from datetime import timedelta
from pathlib import Path
import environ, sys

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="very-secret-key")
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

INV_SERVICE_URL = env('INVENTORY_SERVICE_URL', default="service")

# Приложения
INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'rest_framework',

	# Кастомные
	'apps.product.apps.ProductConfig',
	'apps.promotion.apps.PromotionConfig',
	'apps.chest.apps.ChestConfig',
	'apps.purchase.apps.PurchaseConfig',
	'apps.saga.apps.SagaConfig',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

REST_FRAMEWORK = {
	'DEFAULT_AUTHENTICATION_CLASSES': [
		'rest_framework_simplejwt.authentication.JWTAuthentication',
		# 'config.authentication.AuthServiceAuthentication',
		'config.authentication.XUserIDAuthentication',
	],
	'DEFAULT_PERMISSION_CLASSES': [
		'rest_framework.permissions.IsAuthenticated',
	],
	'DEFAULT_THROTTLE_RATES': {
		'anon': '50/min',
		'user': '50/min'
	}
}



CACHES = {
	"default": {
		"BACKEND": "django_redis.cache.RedisCache",
		"LOCATION": "redis://redis:6379/1",
		"OPTIONS": {
			"CLIENT_CLASS": "django_redis.client.DefaultClient",
		}
	}
}

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
