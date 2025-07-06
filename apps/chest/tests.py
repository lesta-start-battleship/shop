# from django.test import TestCase
# from django.utils import timezone
# from datetime import timedelta
# from apps.chest.models import Chest
# from apps.saga.models import Transaction
#
#
# class ChestModelTest(TestCase):
#     def setUp(self):
#         self.user_id = 1
#         self.chest = Chest.objects.create(
#             name='Test Chest',
#             gold=100,  # обязательное поле
#             currency_type='gold',
#             experience=10,
#             reward_distribution={"gold": 100},
#             daily_purchase_limit=2
#         )
#
#     def test_check_daily_purchase_limit_allows_within_limit(self):
#         Transaction.objects.create(
#             user_id=self.user_id,
#             chest_id=self.chest.id,
#             amount=50,
#             currency_type='gold',
#             status='completed'
#         )
#         is_allowed = self.chest.check_daily_purchase_limit(self.user_id)
#         self.assertTrue(is_allowed)
#
#     def test_check_daily_purchase_limit_blocks_over_limit(self):
#         for _ in range(2):
#             Transaction.objects.create(
#                 user_id=self.user_id,
#                 chest_id=self.chest.id,
#                 amount=50,
#                 currency_type='gold',
#                 status='completed'
#             )
#         is_allowed = self.chest.check_daily_purchase_limit(self.user_id)
#         self.assertFalse(is_allowed)
#
#     def test_check_daily_purchase_limit_ignores_other_users(self):
#         for _ in range(2):
#             Transaction.objects.create(
#                 user_id=self.user_id,
#                 chest_id=self.chest.id,
#                 amount=50,
#                 currency_type='gold',
#                 status='completed'
#             )
#         is_allowed_other = self.chest.check_daily_purchase_limit(user_id=999)
#         self.assertTrue(is_allowed_other)
#
#     def test_check_daily_purchase_limit_ignores_old_transactions(self):
#         past_time = timezone.now() - timedelta(days=1)
#         Transaction.objects.create(
#             user_id=self.user_id,
#             chest_id=self.chest.id,
#             amount=50,
#             currency_type='gold',
#             status='completed',
#             created_at=past_time
#         )
#         is_allowed = self.chest.check_daily_purchase_limit(self.user_id)
#         self.assertTrue(is_allowed)
#
#     def test_check_daily_purchase_limit_allows_if_no_limit(self):
#         chest_no_limit = Chest.objects.create(
#             name='Unlimited Chest',
#             gold=0,
#             currency_type='silver',
#             experience=0,
#             reward_distribution={"silver": 100},
#             daily_purchase_limit=None  # Без лимита
#         )
#         for _ in range(10):
#             Transaction.objects.create(
#                 user_id=self.user_id,
#                 chest_id=chest_no_limit.id,
#                 amount=1,
#                 currency_type='silver',
#                 status='completed'
#             )
#         self.assertTrue(chest_no_limit.check_daily_purchase_limit(self.user_id))
