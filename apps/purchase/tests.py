from django.test import TestCase
from django.utils import timezone
from apps.purchase.models import Purchase
from django.core.exceptions import ValidationError
from unittest.mock import patch


class PurchaseModelTest(TestCase):

    def test_valid_item_purchase(self):
        purchase = Purchase(owner=1, item_id=101)
        purchase.full_clean()
        purchase.save()

        self.assertEqual(Purchase.objects.count(), 1)
        self.assertEqual(purchase.item_id, 101)
        self.assertIn("item", str(purchase))

    def test_valid_chest_purchase(self):
        purchase = Purchase(owner=2, chest_id=202)
        purchase.full_clean()
        purchase.save()

        self.assertEqual(purchase.chest_id, 202)
        self.assertIn("chest", str(purchase))

    def test_valid_promotion_purchase(self):
        purchase = Purchase(owner=3, promotion_id=303)
        purchase.full_clean()
        purchase.save()

        self.assertEqual(purchase.promotion_id, 303)
        self.assertIn("promotion", str(purchase))

    def test_invalid_multiple_fields(self):
        purchase = Purchase(owner=4, item_id=1, chest_id=2)
        with self.assertRaisesMessage(ValidationError, "Ровно одно из полей"):
            purchase.full_clean()

    def test_invalid_no_fields(self):
        purchase = Purchase(owner=5)
        with self.assertRaisesMessage(ValidationError, "Ровно одно из полей"):
            purchase.full_clean()


class PurchaseKafkaTest(TestCase):

    @patch("apps.purchase.models.send_chest_promo_purchase_event")
    def test_kafka_event_sent_for_chest_with_promo(self, mock_send_event):
        purchase = Purchase(owner=1, chest_id=10)
        purchase.full_clean()
        purchase.promotion_id = 20  # добавляем после clean
        purchase.save()

        mock_send_event.assert_called_once_with(1)

    @patch("apps.purchase.models.send_chest_promo_purchase_event")
    def test_kafka_event_not_sent_for_item(self, mock_send_event):
        purchase = Purchase(owner=2, item_id=99)
        purchase.full_clean()
        purchase.save()

        mock_send_event.assert_not_called()

    @patch("apps.purchase.models.send_chest_promo_purchase_event")
    def test_kafka_event_not_sent_for_chest_without_promo(self, mock_send_event):
        purchase = Purchase(owner=3, chest_id=10)
        purchase.full_clean()
        purchase.save()

        mock_send_event.assert_not_called()

    @patch("apps.purchase.models.send_chest_promo_purchase_event")
    def test_kafka_event_not_sent_for_promo_without_chest(self, mock_send_event):
        purchase = Purchase(owner=4, promotion_id=20)
        purchase.full_clean()
        purchase.save()

        mock_send_event.assert_not_called()
