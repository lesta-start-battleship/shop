from django.test import TestCase
from django.utils import timezone
from apps.purchase.models import Purchase


class PurchaseModelTest(TestCase):
    def test_purchase_creation(self):
        purchase = Purchase.objects.create(
            owner=42,
            buy_type="item",
            buy_id=99,
            date=timezone.now()
        )
        self.assertEqual(Purchase.objects.count(), 1)
        self.assertEqual(purchase.owner, 42)
        self.assertEqual(purchase.buy_type, "item")
        self.assertEqual(purchase.buy_id, 99)

    def test_purchase_str_representation(self):
        purchase = Purchase.objects.create(
            owner=7,
            buy_type="promotion",
            buy_id=3,
            date=timezone.now()
        )
        expected_str = "Purchase by user 7: promotion #3"
        self.assertEqual(str(purchase), expected_str)