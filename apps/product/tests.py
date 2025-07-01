from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.product.models import Product

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse


# ----------- МОДЕЛЬНЫЕ ТЕСТЫ -----------

class ProductModelTest(TestCase):

    def setUp(self):
        self.product = Product.objects.create(
            name="Test Product",
            description="Description here",
            cost=100,
            available=True,
            currency_type="gold"  # если в модели есть это поле
        )

    def test_product_creation(self):
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.product.name, "Test Product")
        self.assertTrue(self.product.available)
        self.assertIn("Test Product", str(self.product))

    def test_product_cost_positive(self):
        self.product.cost = -10
        with self.assertRaises(ValidationError):
            self.product.full_clean()  # если есть валидация цены > 0


# ----------- API ТЕСТЫ -----------

class ProductAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.product = Product.objects.create(
            name="API Test Product",
            cost=123,
            available=True,
            currency_type="gold"
        )
        self.list_create_url = reverse("product-list")

    def auth_headers(self, uid=1):
        return {"HTTP_X_USER_ID": str(uid)}

    def test_get_product_list(self):
        response = self.client.get(self.list_create_url, **self.auth_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_create_product(self):
        data = {
            "name": "Created Product",
            "cost": 555,
            "available": True,
            "currency_type": "gold"
        }
        response = self.client.post(self.list_create_url, data, **self.auth_headers())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.filter(name="Created Product").count(), 1)

    def test_create_product_invalid_cost(self):
        data = {
            "name": "Invalid Cost Product",
            "cost": -10,
            "available": True,
            "currency_type": "gold"
        }
        response = self.client.post(self.list_create_url, data, **self.auth_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cost", response.data)

    def test_update_product(self):
        url = reverse("product-detail", kwargs={"pk": self.product.pk})
        data = {"cost": 999}
        response = self.client.patch(url, data, **self.auth_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.cost, 999)

    def test_delete_product(self):
        url = reverse("product-detail", kwargs={"pk": self.product.pk})
        response = self.client.delete(url, **self.auth_headers())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())
