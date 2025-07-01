from datetime import timedelta

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
        self.item = Item.objects.create(
            name="Test Item",
            cost=100,
            currency_type="gold"
        )
        self.chest = Chest.objects.create(
            name="Test Chest",
            gold="100",
            item_probability=0.5,
            currency_type="gold",
            cost=200
        )
        self.promo = Promotion.objects.create(
            name="Test Promo",
            duration=timedelta(days=3),
            price=100.00
        )

    def test_valid_item_purchase_without_promo(self):
        purchase = Purchase(owner=1, item=self.item)
        purchase.full_clean()
        purchase.save()

        self.assertEqual(Purchase.objects.count(), 1)
        self.assertEqual(purchase.item, self.item)
        self.assertIsNone(purchase.promotion)
        self.assertIn("item", str(purchase))

    def test_valid_item_purchase_with_promo(self):
        purchase = Purchase(owner=2, item=self.item, promotion=self.promo)
        purchase.full_clean()
        purchase.save()

        self.assertEqual(purchase.item, self.item)
        self.assertEqual(purchase.promotion, self.promo)

    def test_valid_chest_purchase_without_promo(self):
        purchase = Purchase(owner=3, chest=self.chest)
        purchase.full_clean()
        purchase.save()

        self.assertEqual(purchase.chest, self.chest)
        self.assertIsNone(purchase.promotion)
        self.assertIn("chest", str(purchase))

    def test_valid_chest_purchase_with_promo(self):
        purchase = Purchase(owner=4, chest=self.chest, promotion=self.promo)
        purchase.full_clean()
        purchase.save()

        self.assertEqual(purchase.chest, self.chest)
        self.assertEqual(purchase.promotion, self.promo)

    def test_invalid_multiple_item_and_chest(self):
        purchase = Purchase(owner=5, item=self.item, chest=self.chest)
        with self.assertRaisesMessage(ValidationError, "Ровно одно из полей item или chest должно быть заполнено."):
            purchase.full_clean()

    def test_invalid_no_item_no_chest(self):
        purchase = Purchase(owner=6)
        with self.assertRaisesMessage(ValidationError, "Ровно одно из полей item или chest должно быть заполнено."):
            purchase.full_clean()

    def test_invalid_price_validation(self):
        # Проверяем, что отрицательная цена предмета вызывает ошибку
        self.item.cost = -5
        with self.assertRaises(ValidationError):
            self.item.full_clean()
        purchase = Purchase(owner=7, item=self.item)
        with self.assertRaisesMessage(ValidationError, "Цена предмета должна быть положительной."):
            purchase.full_clean()

        # Аналогично для сундука
        self.chest.cost = 0
        self.chest.save()
        purchase = Purchase(owner=8, chest=self.chest)
        with self.assertRaisesMessage(ValidationError, "Цена сундука должна быть положительной."):
            purchase.full_clean()

        # Аналогично для акции
        self.promo.price = -1
        self.promo.save()
        purchase = Purchase(owner=9, chest=self.chest, promotion=self.promo)
        with self.assertRaisesMessage(ValidationError, "Цена акции должна быть положительной."):
            purchase.full_clean()


# ----------- KAFKA ТЕСТЫ -----------

class PurchaseKafkaTest(TestCase):

    def setUp(self):
        self.chest = Chest.objects.create(
            name="Test Chest",
            gold="100",
            item_probability=0.5,
            currency_type="gold",
            cost=150
        )
        self.promo = Promotion.objects.create(
            name="Test Promo",
            duration=timedelta(days=2),
            price=111.00
        )
        self.item = Item.objects.create(
            name="Test Item",
            cost=123,
            currency_type="gold"
        )

    @patch("apps.purchase.models.send_chest_promo_purchase_event")
    def test_kafka_event_sent_for_chest_with_promo(self, mock_send_event):
        purchase = Purchase(owner=1, chest=self.chest, promotion=self.promo)
        purchase.full_clean()
        purchase.save()

        mock_send_event.assert_called_once_with(1, purchase.quantity)

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
        # Создавать такую покупку запрещено новой логикой, но если пройти - событие не отправится
        with self.assertRaisesMessage(ValidationError, "Ровно одно из полей item или chest должно быть заполнено."):
            purchase.full_clean()
        # purchase.save()  # save не вызовется, ошибка при full_clean()


# ----------- API ТЕСТЫ -----------

class PurchaseAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.item = Item.objects.create(
            name="Test Item",
            cost=77,
            currency_type="gold"
        )
        self.chest = Chest.objects.create(
            name="Test Chest",
            gold="100",
            item_probability=0.5,
            currency_type="gold",
            cost=999
        )
        self.promo = Promotion.objects.create(
            name="Test Promo",
            duration=timedelta(days=4),
            price=150.00
        )
        self.url = reverse("purchase-list-create")

    def auth_headers(self, uid=1):
        return {"HTTP_X_USER_ID": str(uid)}

    def test_create_item_purchase(self):
        response = self.client.post(
            self.url,
            {"item": self.item.id},
            **self.auth_headers(42)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Purchase.objects.count(), 1)
        self.assertEqual(Purchase.objects.first().owner, 42)

    def test_create_item_purchase_with_promo(self):
        response = self.client.post(
            self.url,
            {"item": self.item.id, "promotion": self.promo.id},
            **self.auth_headers(43)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        purchase = Purchase.objects.first()
        self.assertEqual(purchase.owner, 43)
        self.assertEqual(purchase.promotion, self.promo)

    def test_create_chest_promo_purchase(self):
        response = self.client.post(
            self.url,
            {"chest": self.chest.id, "promotion": self.promo.id},
            **self.auth_headers(99)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Purchase.objects.first().owner, 99)

    def test_create_chest_purchase_without_promo(self):
        response = self.client.post(
            self.url,
            {"chest": self.chest.id},
            **self.auth_headers(100)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        purchase = Purchase.objects.first()
        self.assertEqual(purchase.owner, 100)
        self.assertIsNone(purchase.promotion)

    def test_create_invalid_purchase_multiple_fields(self):
        response = self.client.post(
            self.url,
            {"item": self.item.id, "chest": self.chest.id},
            **self.auth_headers()
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Ровно одно из полей", str(response.data))

    def test_create_invalid_purchase_no_fields(self):
        response = self.client.post(
            self.url,
            {},
            **self.auth_headers()
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Ровно одно из полей", str(response.data))

    def test_unauthorized_without_x_user_id(self):
        response = self.client.post(self.url, {"item": self.item.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Missing X-User-ID", response.data["detail"])
