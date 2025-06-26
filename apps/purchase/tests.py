from django.test import TestCase
from django.utils import timezone
from apps.purchase.models import Purchase
from django.core.exceptions import ValidationError


class PurchaseModelTest(TestCase):

    def test_valid_item_purchase(self):
        purchase = Purchase(
            owner=1,
            item_id=101
        )
        purchase.full_clean()  # вызываем валидацию вручную
        purchase.save()

        self.assertEqual(Purchase.objects.count(), 1)
        self.assertEqual(purchase.owner, 1)
        self.assertEqual(purchase.item_id, 101)
        self.assertIsNotNone(purchase.id)
        self.assertIn("item", str(purchase))

    def test_valid_chest_purchase(self):
        purchase = Purchase(
            owner=2,
            chest_id=202
        )
        purchase.full_clean()
        purchase.save()

        self.assertEqual(purchase.chest_id, 202)
        self.assertIsNotNone(purchase.date)
        self.assertIn("chest", str(purchase))

    def test_valid_promotion_purchase(self):
        purchase = Purchase(
            owner=3,
            promotion_id=303
        )
        purchase.full_clean()
        purchase.save()

        self.assertEqual(purchase.promotion_id, 303)
        self.assertGreaterEqual(timezone.now(), purchase.date)
        self.assertIn("promotion", str(purchase))

    def test_invalid_multiple_fields(self):
        purchase = Purchase(
            owner=4,
            item_id=1,
            chest_id=2
        )
        with self.assertRaisesMessage(ValidationError, "Ровно одно из полей"):
            purchase.full_clean()

    def test_invalid_no_fields(self):
        purchase = Purchase(owner=5)
        with self.assertRaisesMessage(ValidationError, "Ровно одно из полей"):
            purchase.full_clean()
