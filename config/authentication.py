from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth.models import AnonymousUser
from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()

class XUserIDAuthentication(authentication.BaseAuthentication):
    """
    Аутентификация по заголовку X-User-ID, без пароля.
    Пользователь автоматически создаётся/загружается по UID.
    """

    def authenticate(self, request):
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return None

        try:
            user_id_int = int(user_id)
        except ValueError:
            raise exceptions.AuthenticationFailed("Invalid X-User-ID header")

        user, created = User.objects.get_or_create(id=user_id_int, defaults={"username": f"user_{user_id_int}"})

        return (user, None)

class IsAuthenticatedViaXUserID(permissions.BasePermission):
    """
    Разрешает доступ только аутентифицированным через X-User-ID.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

# import time
# import jwt
# import requests
# from django.core.cache import cache
# from rest_framework.authentication import BaseAuthentication
# from rest_framework.exceptions import AuthenticationFailed
#
# AUTH_VERIFY_URL = "http://auth-service/api/auth/verify-token/"
# MAX_CACHE_TTL = 180
#
#
# class AuthServiceAuthentication(BaseAuthentication):
# 	def authenticate(self, request):
# 		token = request.headers.get('Authorization')
# 		if not token:
# 			raise AuthenticationFailed('Authorization header required')
#
# 		token = token.strip()
# 		if not token.startswith("Bearer "):
# 			raise AuthenticationFailed('Invalid token format')
#
# 		# Ключ кэша — сам токен
# 		raw_token = token.split(" ", 1)[1]
# 		cached_data = cache.get(token)
#
# 		if cached_data:
# 			request.auth = raw_token
# 			return (cached_data, None)
#
# 		# Запрос в auth-сервис
# 		try:
# 			response = requests.get(
# 				AUTH_VERIFY_URL,
# 				headers={'Authorization': token},
# 				timeout=2
# 			)
# 		except requests.RequestException:
# 			raise AuthenticationFailed('Auth service unavailable')
#
# 		if response.status_code != 200:
# 			raise AuthenticationFailed('Invalid or expired token')
#
# 		user_data = response.json()
#
# 		ttl = self._cache_ttl_seconds(raw_token)
# 		if ttl > 0:
# 			cache.set(token, user_data, timeout=ttl)
#
# 		request.auth = raw_token
# 		return (user_data, None)
#
# 	def _cache_ttl_seconds(self, token: str) -> int:
# 		try:
# 			decoded = jwt.decode(token, options={"verify_signature": False})
# 			exp = decoded.get("exp")
# 			if not exp:
# 				return 0
# 			now = int(time.time())
# 			ttl = exp - now
# 			if ttl <= 0:
# 				return 0
# 			return min(ttl, MAX_CACHE_TTL)
# 		except Exception:
# 			return 0
