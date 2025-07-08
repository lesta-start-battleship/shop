# from django.test import TestCase
# from rest_framework.test import APIClient
# from rest_framework import status
# from unittest.mock import MagicMock
# from apps.chest.models import Chest
# from apps.product.models import Product
#
#
# class ChestViewsTest(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#
#         self.user_mock = MagicMock()
#         self.user_mock.is_authenticated = True
#         self.user_mock.role = "user"
#         self.client.force_authenticate(user=self.user_mock)
#
#         self.chest = Chest.objects.create(
#             name="Starter Chest",
#             gold=50,
#             item_probability=0.5,
#             cost=100,
#             currency_type="gold",
#             daily_purchase_limit=2,
#             experience=10,
#         )
#
#     def test_get_chest_list(self):
#         response = self.client.get("/chest/")
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_get_chest_detail(self):
#         response = self.client.get(f"/chest/{self.chest.id}/")
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_buy_chest_success(self):
#         response = self.client.post(f"/chest/{self.chest.id}/buy/")
#         self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
#
#     def test_buy_chest_limit_exceeded(self):
#         # Покупаем дважды (лимит 2), потом третий раз — ошибка
#         self.client.post(f"/chest/{self.chest.id}/buy/")
#         self.client.post(f"/chest/{self.chest.id}/buy/")
#         response = self.client.post(f"/chest/{self.chest.id}/buy/")
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("Превышен дневной лимит", response.json().get("error", ""))
#
#
# class AdminProductTests(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#
#         self.admin_mock = MagicMock()
#         self.admin_mock.is_authenticated = True
#         self.admin_mock.role = "admin"
#         self.client.force_authenticate(user=self.admin_mock)
#
#         self.product = Product.objects.create(
#             name="Epic Sword",
#             description="Strong weapon",
#             currency_type="gold",
#             cost=500,
#             daily_purchase_limit=3,
#         )
#
#     def test_admin_can_get_product_list(self):
#         response = self.client.get("/admin/products/")
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_admin_can_get_product_detail(self):
#         response = self.client.get(f"/admin/products/{self.product.id}/")
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
