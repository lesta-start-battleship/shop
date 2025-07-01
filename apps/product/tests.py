from django.test import TestCase
from unittest.mock import patch

from apps.product.models import Product
from apps.purchase.models import Purchase


# ----------- МОДЕЛЬНЫЕ ТЕСТЫ -----------

class ProductModelTest(TestCase):

    def setUp(self):
        self.product = Product.objects.create(
            name="Test Product",
            description="Description here",
            price=100,
            available=True,
        )

    def test_product_creation(self):
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.product.name, "Test Product")
        self.assertTrue(self.product.available)
        self.assertIn("Test Product", str(self.product))

    def test_product_price_positive(self):
        self.product.price = -10
        with self.assertRaises(Exception):
            self.product.full_clean()  # если есть валидация цены > 0


# ----------- KAFKA ТЕСТЫ -----------

class ProductKafkaTest(TestCase):

    def setUp(self):
        self.product = Product.objects.create(
            name="Kafka Test Product",
            price=200,
            available=True,
        )

    @patch("apps.product.models.send_product_event")
    def test_kafka_event_sent_on_product_creation(self, mock_send_event):
        product = Product(
            name="New Kafka Product",
            price=150,
            available=True,
        )
        product.full_clean()
        product.save()

        mock_send_event.assert_called_once_with(product.id)

    @patch("apps.product.models.send_product_event")
    def test_kafka_event_sent_on_product_update(self, mock_send_event):
        self.product.name = "Updated Name"
        self.product.save()

        mock_send_event.assert_called_once_with(self.product.id)

    @patch("apps.product.models.send_product_event")
    def test_kafka_event_not_sent_if_product_unavailable(self, mock_send_event):
        self.product.available = False
        self.product.save()

        # Допустим, что при unavailable событие не отправляется
        mock_send_event.assert_not_called()


# ----------- API ТЕСТЫ -----------

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse


class ProductAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.product = Product.objects.create(
            name="API Test Product",
            price=123,
            available=True,
        )
        self.list_create_url = reverse("product-list-create")  # имя роута из urls.py

    def test_get_product_list(self):
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_create_product(self):
        data = {
            "name": "Created Product",
            "price": 555,
            "available": True,
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.filter(name="Created Product").count(), 1)

    def test_create_product_invalid_price(self):
        data = {
            "name": "Invalid Price Product",
            "price": -10,
            "available": True,
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data)

    def test_update_product(self):
        url = reverse("product-detail", kwargs={"pk": self.product.pk})
        data = {"price": 999}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, 999)

    def test_delete_product(self):
        url = reverse("product-detail", kwargs={"pk": self.product.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())
