import logging

logger = logging.getLogger(__name__)


def get_inventory_headers(request=None):
	if request:
		auth_header = request.headers.get('Authorization', '')

		if not auth_header.startswith('Bearer '):
			if hasattr(request, 'auth') and request.auth:
				auth_header = f"Bearer {request.auth}"
			else:
				raise Exception("Authentication credentials were not provided")

		return {
			'Authorization': auth_header,
			'Content-Type': 'application/json'
		}
