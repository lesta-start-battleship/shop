import requests
from django.conf import settings

# Inventory Service Wrapper
class InventoryService:
    
    @staticmethod
    def get_inventories_with_item(item_id):
        url = f"{settings.INV_SERVICE_URL}/inventory/all_inventory_with_item/{item_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def delete_item(item_id):
        url = f"{settings.INV_SERVICE_URL}/inventory/items/{item_id}"
        response = requests.delete(url)
        response.raise_for_status()
        return response.json()


# Auth Service Wrapper
class AuthService:
    
    @staticmethod
    def compensate_balance(user_id, amount, currency):
        url = f"{settings.AUTH_SERVICE_URL}/auth/compensate_balance"
        payload = {
            "user_id": user_id,
            "amount": amount,
            "currency": currency
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()