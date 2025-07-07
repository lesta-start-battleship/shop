from django.test import TestCase, override_settings
from apps.product.models import Product
from apps.chest.models import Chest
from apps.promotion.models import Promotion
from apps.saga.models import Transaction
from apps.purchase.models import Purchase
from apps.saga.saga_orchestrator import start_purchase, handle_authorization_response
from unittest.mock import patch, MagicMock
from datetime import timedelta
import uuid


class TransactionTestCase(TestCase):

    def setUp(self):
        self.user_id = 123
        self.promotion = Promotion.objects.create(
            name="Promo",
            description="Test Promo",
            duration=timedelta(days=7)
        )
        self.product = Product.objects.create(
            name="Test Product",
            description="Desc",
            cost=100,
            currency_type="gold",
            daily_purchase_limit=5,
            promotion=self.promotion
        )
        self.chest = Chest.objects.create(
            name="Silver Chest",
            currency_type="gold",
            cost=200,
            daily_purchase_limit=10,
            reward_distribution={"gold": 1.0},
            experience=1,
            gold=100,
            item_probability=50,
            promotion=self.promotion
        )

    @override_settings(INVENTORY_SERVICE_URL='http://inventory.local')
    @patch("apps.saga.saga_orchestrator.requests.Session.patch")
    def test_successful_product_transaction(self, mock_patch):
        mock_patch.return_value.status_code = 200
        transaction = start_purchase(
            user_id=self.user_id,
            amount=self.product.cost,
            currency_type="gold",
            product_id=self.product.id,
            promotion_id=self.promotion.id
        )

        kafka_msg = MagicMock()
        kafka_msg.value.return_value = bytes(
            f'{{"transaction_id": "{transaction.id}", "success": true}}',
            encoding='utf-8'
        )

        handle_authorization_response(kafka_msg)

        transaction.refresh_from_db()
        self.assertEqual(transaction.status, "COMPLETED")
        self.assertTrue(Purchase.objects.filter(item=self.product, owner=self.user_id).exists())

    @override_settings(INVENTORY_SERVICE_URL='http://inventory.local')
    @patch("apps.saga.saga_orchestrator.requests.Session.patch")
    def test_successful_chest_transaction(self, mock_patch):
        mock_patch.return_value.status_code = 200
        transaction = start_purchase(
            user_id=self.user_id,
            amount=self.chest.cost,
            currency_type="gold",
            chest_id=self.chest.id,
            promotion_id=self.promotion.id
        )

        kafka_msg = MagicMock()
        kafka_msg.value.return_value = bytes(
            f'{{"transaction_id": "{transaction.id}", "success": true}}',
            encoding='utf-8'
        )

        handle_authorization_response(kafka_msg)

        transaction.refresh_from_db()
        self.assertEqual(transaction.status, "COMPLETED")
        self.assertTrue(Purchase.objects.filter(chest=self.chest, owner=self.user_id).exists())

    def test_failed_transaction(self):
        transaction = Transaction.objects.create(
            id=uuid.uuid4(),
            user_id=self.user_id,
            amount=9999,
            currency_type="gold",
            product_id=self.product.id,
            promotion_id=self.promotion.id,
            status="PENDING"
        )

        kafka_msg = MagicMock()
        kafka_msg.value.return_value = bytes(
            f'{{"transaction_id": "{transaction.id}", "success": false, "code": "insufficient_funds"}}',
            encoding='utf-8'
        )

        handle_authorization_response(kafka_msg)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, "DECLINED")
        self.assertIn("Not enough money", transaction.error_message)

    def test_purchase_not_created_on_failed_transaction(self):
        transaction = Transaction.objects.create(
            id=uuid.uuid4(),
            user_id=self.user_id,
            amount=9999,
            currency_type="gold",
            product_id=self.product.id,
            promotion_id=self.promotion.id,
            status="PENDING"
        )

        kafka_msg = MagicMock()
        kafka_msg.value.return_value = bytes(
            f'{{"transaction_id": "{transaction.id}", "success": false, "code": "insufficient_funds"}}',
            encoding='utf-8'
        )

        handle_authorization_response(kafka_msg)
        transaction.refresh_from_db()

        self.assertEqual(transaction.status, "DECLINED")
        self.assertFalse(Purchase.objects.filter(item=self.product, owner=self.user_id).exists())

    def test_multiple_transactions_limit_respected(self):
        for _ in range(self.product.daily_purchase_limit):
            Transaction.objects.create(
                user_id=self.user_id,
                product_id=self.product.id,
                promotion_id=self.promotion.id,
                amount=self.product.cost,
                currency_type="gold",
                status="COMPLETED"
            )
        transaction = start_purchase(
            user_id=self.user_id,
            amount=self.product.cost,
            currency_type="gold",
            product_id=self.product.id,
            promotion_id=self.promotion.id
        )
        self.assertEqual(transaction.status, "PENDING")

    @override_settings(INVENTORY_SERVICE_URL='http://inventory.local')
    @patch("apps.saga.saga_orchestrator.requests.Session.patch")
    def test_transaction_status_updates_correctly(self, mock_patch):
        mock_patch.return_value.status_code = 200

        transaction = start_purchase(
            user_id=self.user_id,
            amount=self.product.cost,
            currency_type="gold",
            product_id=self.product.id,
            promotion_id=self.promotion.id
        )

        self.assertEqual(transaction.status, "PENDING")

        kafka_msg = MagicMock()
        kafka_msg.value.return_value = bytes(
            f'{{"transaction_id": "{transaction.id}", "success": true}}',
            encoding='utf-8'
        )

        handle_authorization_response(kafka_msg)

        transaction.refresh_from_db()
        self.assertEqual(transaction.status, "COMPLETED")

    @override_settings(INVENTORY_SERVICE_URL='http://inventory.local')
    @patch("apps.saga.saga_orchestrator.requests.Session.patch")
    def test_purchase_created_with_correct_data(self, mock_patch):
        mock_patch.return_value.status_code = 200

        transaction = start_purchase(
            user_id=self.user_id,
            amount=self.product.cost,
            currency_type="gold",
            product_id=self.product.id,
            promotion_id=self.promotion.id
        )

        kafka_msg = MagicMock()
        kafka_msg.value.return_value = bytes(
            f'{{"transaction_id": "{transaction.id}", "success": true}}',
            encoding='utf-8'
        )

        handle_authorization_response(kafka_msg)

        purchase = Purchase.objects.get(item=self.product, owner=self.user_id)

        self.assertEqual(purchase.item, self.product)
        self.assertEqual(purchase.owner, self.user_id)
        self.assertEqual(purchase.promotion, self.promotion)
        self.assertIsNone(purchase.chest)
