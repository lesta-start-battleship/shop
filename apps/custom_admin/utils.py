import requests

from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_inventory_service_headers(request):
	if not request.auth:
		raise Exception("Authentication credentials were not provided")

	auth_header = request.headers.get('Authorization', '')
	if auth_header.startswith('Bearer '):
		return {
			'Authorization': auth_header,
			'Content-Type': 'application/json'
		}
	raise Exception("Invalid authorization header")


def create_inventory_item(request, chest_data):
	try:
		item_data = {
			"name": chest_data.get('name'),
			"description": f"Сундук: {chest_data.get('name')}",
			"kind": "chest",
			"properties": {
				"gold": chest_data.get('gold', 0),
				"experience": chest_data.get('experience', 0),
				"reward_distribution": chest_data.get('reward_distribution', {})
			}
		}

		response = requests.post(
			f"{settings.INVENTORY_SERVICE_URL}/items/create",
			json=item_data,
			headers=get_inventory_service_headers(request),
			timeout=settings.INVENTORY_SERVICE_TIMEOUT
		)

		if response.status_code != 201:
			raise Exception(f"Inventory service error: {response.text}")

		return response.json().get('id')

	except Exception as e:
		raise


def delete_inventory_item(request, item_id):
	try:
		response = requests.delete(
			f"{settings.INVENTORY_SERVICE_URL}/items/{item_id}",
			headers=get_inventory_service_headers(request),
			timeout=settings.INVENTORY_SERVICE_TIMEOUT
		)

		if response.status_code != 204:
			logger.warning(f"Inventory item deletion warning: {response.text}")

	except Exception as e:
		logger.error(f"Error deleting inventory item: {str(e)}")
		raise
