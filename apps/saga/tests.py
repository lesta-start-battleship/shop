import json
import logging
import uuid
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from apps.product.models import Product
from apps.chest.models import Chest
from apps.promotion.models import Promotion
from apps.purchase.models import Purchase
from apps.saga.models import Transaction
from apps.saga.saga_orchestrator import start_purchase, handle_authorization_response


logger = logging.getLogger(__name__)


# ===== Transaction Saga Tests =====

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
            cost=self.product.cost,
            currency_type="gold",
            product_id=self.product.id,
            promotion_id=self.promotion.id
        )

        kafka_msg = MagicMock()
        kafka_msg.value.return_value = json.dumps({
            "transaction_id": str(transaction.id),
            "success": True
        }).encode("utf-8")

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
            cost=self.chest.cost,
            currency_type="gold",
            chest_id=self.chest.id,
            promotion_id=self.promotion.id
        )

        kafka_msg = MagicMock()
        kafka_msg.value.return_value = json.dumps({
            "transaction_id": str(transaction.id),
            "success": True
        }).encode("utf-8")

        handle_authorization_response(kafka_msg)

        transaction.refresh_from_db()
        self.assertEqual(transaction.status, "COMPLETED")
        self.assertTrue(Purchase.objects.filter(chest=self.chest, owner=self.user_id).exists())

    def test_failed_transaction(self):
        transaction = Transaction.objects.create(
            id=uuid.uuid4(),
            user_id=self.user_id,
            cost=9999,
            currency_type="gold",
            product_id=self.product.id,
            promotion_id=self.promotion.id,
            status="pending"
        )

        kafka_msg = MagicMock()
        kafka_msg.value.return_value = json.dumps({
            "transaction_id": str(transaction.id),
            "success": False,
            "code": "insufficient_funds"
        }).encode("utf-8")

        handle_authorization_response(kafka_msg)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, "DECLINED")
        self.assertIn("Not enough money", transaction.error_message)

    def test_purchase_not_created_on_failed_transaction(self):
        transaction = Transaction.objects.create(
            id=uuid.uuid4(),
            user_id=self.user_id,
            cost=9999,
            currency_type="gold",
            product_id=self.product.id,
            promotion_id=self.promotion.id,
            status="pending"
        )

        kafka_msg = MagicMock()
        kafka_msg.value.return_value = json.dumps({
            "transaction_id": str(transaction.id),
            "success": False,
            "code": "insufficient_funds"
        }).encode("utf-8")

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
                cost=self.product.cost,
                currency_type="gold",
                status="COMPLETED"
            )
        transaction = start_purchase(
            user_id=self.user_id,
            cost=self.product.cost,
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
            cost=self.product.cost,
            currency_type="gold",
            product_id=self.product.id,
            promotion_id=self.promotion.id
        )

        self.assertEqual(transaction.status, "PENDING")

        kafka_msg = MagicMock()
        kafka_msg.value.return_value = json.dumps({
            "transaction_id": str(transaction.id),
            "success": True
        }).encode("utf-8")

        handle_authorization_response(kafka_msg)

        transaction.refresh_from_db()
        self.assertEqual(transaction.status, "COMPLETED")

    @override_settings(INVENTORY_SERVICE_URL='http://inventory.local')
    @patch("apps.saga.saga_orchestrator.requests.Session.patch")
    def test_purchase_created_with_correct_data(self, mock_patch):
        mock_patch.return_value.status_code = 200

        transaction = start_purchase(
            user_id=self.user_id,
            cost=self.product.cost,
            currency_type="gold",
            product_id=self.product.id,
            promotion_id=self.promotion.id
        )

        kafka_msg = MagicMock()
        kafka_msg.value.return_value = json.dumps({
            "transaction_id": str(transaction.id),
            "success": True
        }).encode("utf-8")

        handle_authorization_response(kafka_msg)

        purchase = Purchase.objects.get(item=self.product, owner=self.user_id)

        self.assertEqual(purchase.item, self.product)
        self.assertEqual(purchase.owner, self.user_id)
        self.assertEqual(purchase.promotion, self.promotion)
        self.assertIsNone(purchase.chest)


# ===== Kafka message dispatching =====

def process_single_kafka_message(msg):
    from .saga_orchestrator import safe_json_decode
    from apps.chest.tasks import (
        handle_guild_war_match_result,
        handle_guild_war_game_result,
    )
    from kafka.handlers import handle_inventory_update
    from .saga_orchestrator import (
        handle_authorization_response,
        handle_compensation_response,
        handle_promotion_compensation_response
    )

    if msg.error():
        return

    topic = msg.topic()
    data = safe_json_decode(msg)
    if data is None:
        return

    if topic == 'auth.balance.reserve.response.shop':
        handle_authorization_response(msg)
    elif topic == 'auth.balance.compensate.response.shop':
        handle_compensation_response(msg)
    elif topic == 'shop.inventory.updates':
        handle_inventory_update(data)
    elif topic == 'balance-responses':
        handle_authorization_response(msg)
    elif topic == 'compensation-responses':
        handle_compensation_response(msg)
    elif topic == 'stage.game.fact.match-results.v1':
        handle_guild_war_match_result.delay(data)
    elif topic == 'prod.scoreboard.fact.guild-war.1':
        handle_guild_war_game_result.delay(data)
    elif topic == 'promotion.compensation.commands':
        handle_promotion_compensation_response(msg)
    else:
        logger.warning(f"Unknown topic: {topic}")


class KafkaMessageHandlerTestCase(TestCase):

    def _make_mock_message(self, topic: str, value: dict):
        msg = MagicMock()
        msg.topic.return_value = topic
        msg.value.return_value = json.dumps(value).encode("utf-8")
        msg.error.return_value = None
        return msg

    @patch("apps.saga.saga_orchestrator.handle_authorization_response")
    def test_auth_balance_reserve_handler(self, mock_handler):
        msg = self._make_mock_message("auth.balance.reserve.response.shop", {
            "transaction_id": "abc", "success": True
        })
        process_single_kafka_message(msg)
        mock_handler.assert_called_once_with(msg)

    @patch("apps.saga.saga_orchestrator.handle_compensation_response")
    def test_auth_balance_compensate_handler(self, mock_handler):
        msg = self._make_mock_message("auth.balance.compensate.response.shop", {
            "transaction_id": "abc", "success": True
        })
        process_single_kafka_message(msg)
        mock_handler.assert_called_once_with(msg)

    @patch("apps.saga.saga_orchestrator.handle_authorization_response")
    def test_legacy_balance_responses_handler(self, mock_handler):
        msg = self._make_mock_message("balance-responses", {
            "transaction_id": "abc", "success": True
        })
        process_single_kafka_message(msg)
        mock_handler.assert_called_once_with(msg)

    @patch("apps.saga.saga_orchestrator.handle_compensation_response")
    def test_legacy_compensation_responses_handler(self, mock_handler):
        msg = self._make_mock_message("compensation-responses", {
            "transaction_id": "abc", "success": False
        })
        process_single_kafka_message(msg)
        mock_handler.assert_called_once_with(msg)

    @patch("kafka.handlers.handle_inventory_update")
    def test_inventory_update_handler(self, mock_handler):
        msg = self._make_mock_message("shop.inventory.updates", {
            "id": 1, "name": "Sword", "currency_type": "gold"
        })
        process_single_kafka_message(msg)
        mock_handler.assert_called_once_with({
            "id": 1, "name": "Sword", "currency_type": "gold"
        })

    @patch("apps.chest.tasks.handle_guild_war_match_result.delay")
    def test_match_result_handler(self, mock_handler):
        msg = self._make_mock_message("stage.game.fact.match-results.v1", {
            "match_id": 42
        })
        process_single_kafka_message(msg)
        mock_handler.assert_called_once_with({"match_id": 42})

    @patch("apps.chest.tasks.handle_guild_war_game_result.delay")
    def test_guild_war_handler(self, mock_handler):
        msg = self._make_mock_message("prod.scoreboard.fact.guild-war.1", {
            "war_id": 99
        })
        process_single_kafka_message(msg)
        mock_handler.assert_called_once_with({"war_id": 99})

    @patch("apps.saga.saga_orchestrator.handle_promotion_compensation_response")
    def test_promotion_compensation_handler(self, mock_handler):
        msg = self._make_mock_message("promotion.compensation.commands", {
            "user_id": 1, "item_id": 77, "success": True
        })
        process_single_kafka_message(msg)
        mock_handler.assert_called_once_with(msg)

    @patch("apps.saga.tests.logger.warning")
    def test_unknown_topic_logs_warning(self, mock_warning):
        msg = self._make_mock_message("unknown.topic.name", {
            "foo": "bar"
        })
        process_single_kafka_message(msg)
        mock_warning.assert_called_once_with("Unknown topic: unknown.topic.name")
