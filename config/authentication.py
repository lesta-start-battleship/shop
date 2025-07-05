import jwt
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed


class GatewayUser:
	def __init__(self, user_id, username, role):
		self.id = user_id
		self.username = username
		self.role = role
		self.is_authenticated = True


class GatewayJWTAuthentication(authentication.BaseAuthentication):
	def authenticate(self, request):
		auth_header = request.headers.get('Authorization', '')
		if auth_header.startswith('Bearer '):
			token = auth_header.split(' ')[1]
		else:
			token = auth_header.strip()

		if not token:
			return None

		try:
			payload = jwt.decode(token, options={"verify_signature": False})

			# Ensure user_id is always an integer
			user_id = int(payload.get('sub')) if payload.get('sub') else None

			user = GatewayUser(
				user_id=user_id,
				username=payload.get('username'),
				role=payload.get('role', 'user')
			)

			return (user, None)

		except (jwt.DecodeError, ValueError) as e:
			raise AuthenticationFailed('Invalid token format')
		except Exception as e:
			raise AuthenticationFailed(f'Authentication failed: {str(e)}')
