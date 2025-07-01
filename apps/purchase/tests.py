from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from unittest.mock import patch

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse

from apps.purchase.models import Purchase
from apps.product.models import Product as Item
from apps.chest.models import Chest
from apps.promotion.models import Promotion


# ----------- МОДЕЛЬНЫЕ ТЕСТЫ -----------

class PurchaseModelTest(TestCase):

    def setUp(self):
        self.item = Item.objects.create(name="Test Item")
        self.chest = Chest.objects.create(name="Test Chest")
        self.promo = Promotion.objects.create(title="Test Promo")

    def test_valid_item_purchase(self):
        purchase = Purchase(owner=1, item=self.item)
        purchase.full_clean()
        purchase.save()

        self.assertEqual(Purchase.objects.count(), 1)
        self.assertEqual(purchase.item, self.item)
        self.assertIn("item", str(purchase))

    def test_valid_chest_purchase(self):
        purchase = Purchase(owner=2, chest=self.chest)
        purchase.full_clean()
        purchase.save()

        self.assertEqual(purchase.chest, self.chest)
        self.assertIn("chest", str(purchase))

    def test_valid_promotion_purchase(self):
        purchase = Purchase(owner=3, promotion=self.promo)
        purchase.full_clean()
        purchase.save()

        self.assertEqual(purchase.promotion, self.promo)
        self.assertGreaterEqual(timezone.now(), purchase.date)
        self.assertIn("promotion", str(purchase))

    def test_invalid_multiple_fields(self):
        purchase = Purchase(owner=4, item=self.item, chest=self.chest)
        with self.assertRaisesMessage(ValidationError, "Ровно одно из полей"):
            purchase.full_clean()

    def test_invalid_no_fields(self):
        purchase = Purchase(owner=5)
        with self.assertRaisesMessage(ValidationError, "Ровно одно из полей"):
            purchase.full_clean()


# ----------- KAFKA ТЕСТЫ -----------

class PurchaseKafkaTest(TestCase):

    def setUp(self):
        self.chest = Chest.objects.create(name="Test Chest")
        self.promo = Promotion.objects.create(title="Test Promo")
        self.item = Item.objects.create(name="Test Item")

    @patch("apps.purchase.models.send_chest_promo_purchase_event")
    def test_kafka_event_sent_for_chest_with_promo(self, mock_send_event):
        purchase = Purchase(owner=1, chest=self.chest, promotion=self.promo)
        purchase.full_clean()
        purchase.save()

        mock_send_event.assert_called_once_with(1)

    @patch("apps.purchase.models.send_chest_promo_purchase_event")
    def test_kafka_event_not_sent_for_item(self, mock_send_event):
        purchase = Purchase(owner=2, item=self.item)
        purchase.full_clean()
        purchase.save()

        mock_send_event.assert_not_called()

    @patch("apps.purchase.models.send_chest_promo_purchase_event")
    def test_kafka_event_not_sent_for_chest_without_promo(self, mock_send_event):
        purchase = Purchase(owner=3, chest=self.chest)
        purchase.full_clean()
        purchase.save()

        mock_send_event.assert_not_called()

    @patch("apps.purchase.models.send_chest_promo_purchase_event")
    def test_kafka_event_not_sent_for_promo_without_chest(self, mock_send_event):
        purchase = Purchase(owner=4, promotion=self.promo)
        purchase.full_clean()
        purchase.save()

        mock_send_event.assert_not_called()


# ----------- API ТЕСТЫ -----------

class PurchaseAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.item = Item.objects.create(name="Test Item")
        self.chest = Chest.objects.create(name="Test Chest")
        self.promo = Promotion.objects.create(title="Test Promo")
        self.url = reverse("purchase-list-create")

    def test_create_item_purchase(self):
        response = self.client.post(
            self.url,
            {"item": self.item.id},
            HTTP_X_USER_ID="42"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Purchase.objects.count(), 1)
        self.assertEqual(Purchase.objects.first().owner, 42)

    def test_create_chest_promo_purchase(self):
        response = self.client.post(
            self.url,
            {"chest": self.chest.id, "promotion": self.promo.id},
            HTTP_X_USER_ID="99"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Purchase.objects.first().owner, 99)

    def test_create_invalid_purchase_multiple_fields(self):
        response = self.client.post(
            self.url,
            {"item": self.item.id, "chest": self.chest.id},
            HTTP_X_USER_ID="1"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Ровно одно из полей", str(response.data))

    def test_create_invalid_purchase_no_fields(self):
        response = self.client.post(
            self.url,
            {},
            HTTP_X_USER_ID="1"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Ровно одно из полей", str(response.data))

    def test_unauthorized_without_x_user_id(self):
        response = self.client.post(self.url, {"item": self.item.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Missing X-User-ID", response.data["detail"])
