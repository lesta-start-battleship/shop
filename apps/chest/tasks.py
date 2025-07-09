import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import requests
from celery import shared_task, group
from django.utils import timezone
from rest_framework.generics import get_object_or_404

from apps.chest.models import Chest, ChestOpeningDistribution
from apps.chest.utils import open_chest, generate_token, send_guild_war_reward, get_chest_settings
from apps.saga.saga_orchestrator import get_producer
from config import settings

logger = logging.getLogger(__name__)

INVENTORY_API_URL = settings.INVENTORY_SERVICE_URL
AUTH_API_URL = settings.AUTH_SERVICE_URL
GUILD_API_URL = settings.GUILD_API_URL


@shared_task(bind=True, max_retries=3)
def open_chest_task(self, distribution_id):
    logger.info("Open chest celery task started")

    try:
        distribution: ChestOpeningDistribution = ChestOpeningDistribution.objects.get(id=distribution_id)
        distribution.retry += 1
        distribution.save()

        if distribution.status == 'pending':
            # Headers with received token
            headers = {
                "Authorization": f"Bearer {distribution.token}",
                "Content-Type": "application/json"
            }

            # Open chest in inventory
            open_chest_url = f"{INVENTORY_API_URL}/inventory/use_item/"
            open_response = requests.patch(
                open_chest_url,
                json={
                    "item_id": distribution.chest_id,
                    "amount": distribution.amount
                },
                headers=headers
            )
            open_response.raise_for_status()
            distribution.status = 'chest_used'
            distribution.save()

        if distribution.status == 'chest_used':
            # Open claimed chests
            chest = Chest.objects.filter(item_id=distribution.chest_id).prefetch_related('product').first()

            rewards = open_chest(chest, distribution.amount)
            distribution.rewards = rewards
            distribution.status = 'rewards_generated'
            distribution.save()

        if distribution.status == 'rewards_generated':
            send_to_inventory_service(distribution.rewards, distribution.token)

            distribution.status = 'items_sent'
            distribution.save()

        if distribution.status == 'items_sent':
            send_to_user_service(distribution.rewards)

            distribution.status = 'gold_sent'
            distribution.save()

        if distribution.status == 'gold_sent':

            if distribution.rewards.get('promo_chests'):
                send_chest_event_to_kafka.delay(distribution.rewards['promo_chests'], distribution.user_id)

            distribution.status = 'scoreboard_sent'
            distribution.save()

        # if callback_url:
        #     send_callback.delay(rewards, callback_url, token)

        if distribution.status == 'scoreboard_sent':
            distribution.status = 'completed'

            distribution.save()

    except Exception as e:
        logger.error(f"Error in open_chest_task: {str(e)}")

        distribution.status = 'failed'
        distribution.save()

        self.retry(exc=e)



@shared_task
def send_to_inventory_service(result_data, token):
    """Celery task for send result about items to inventory"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    inventory_response_url = f"{INVENTORY_API_URL}/inventory/add_item/"

    for item_id, amount in result_data["products_id"].items():
        requests.patch(
            inventory_response_url,
            json={
                "item_id": item_id,
                "amount": amount
            },
            headers=headers
        )


@shared_task
def send_to_user_service(result_data, token):
    """Celery task for send result about gold to user"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    inventory_response_url = f"{AUTH_API_URL}/api/v1/currencies/"
    gold = result_data.get("gold", 0)
    if gold > 0:
        requests.patch(
            inventory_response_url,
            json={
                "gold": gold,
                "guild_rage": 0
            },
            headers=headers
        )


@shared_task(bind=True, max_retries=3)
def send_callback(self, result_data, callback_url, token):
    """Send message to successful callback_url"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            callback_url,
            json={
                "status": "success",
                "rewards": result_data["callback_rewards"]
            },
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Callback failed: {str(e)}")
        self.retry(exc=e, countdown=10)


def distribute_chest_opening_result(rewards, token):
    """Group of tasks for celery"""
    task_group = group(send_to_inventory_service.s(rewards, token), send_to_user_service.s(rewards, token))

    task_group.apply_async()


@shared_task
def send_chest_event_to_kafka(chests, user_id):
    """Send chests open event to scoreboard Kafka"""
    producer = get_producer()
    topic = settings.KAFKA_CHEST_EVENTS_TOPIC
    for chest in chests:
        try:
            chest = {"user_id": user_id, "promo": chest[0], "exp": chest[1]}
            serialized = json.dumps(chest, ensure_ascii=False).encode('utf-8')
            producer.produce(topic, value=serialized)
            logger.debug(f"Sent event: {chest}")
        except Exception as e:
            logger.error(f"Error: {str(e)}")

    producer.flush()
    logger.info(f"Sent {len(chests)} events in Kafka")


@shared_task
def recover_stuck_distribution():
    time = timezone.now() - timedelta(minutes=10)

    stuck_distributions = ChestOpeningDistribution.objects.filter(
        updated_at__lt=time,
        status__in=['pending', 'chest_used', 'rewards_generated', 'items_sent', 'gold_sent', 'kafka_sent']
    )

    for distribution in stuck_distributions:
        open_chest_task.delay(distribution.id)

    failed_distributions = ChestOpeningDistribution.objects.filter(
        status='failed',
        retry_count__lt=3
    )

    for distribution in failed_distributions:
        open_chest_task.delay(distribution.id)


@shared_task(bind=True)
def handle_guild_war_match_result(self, event: dict):
    logger.info(f"winner {event}")
    winner_id = event.get("winner_id")
    loser_id = event.get("loser_id")
    match_type = event.get("match_type")

    chest_settings = get_chest_settings()

    guild_war_chest_name = chest_settings.guild_war_participant_chest

    if match_type != "guild_war":
        return

    logger.info(f"winner {winner_id}, loser {loser_id}, match_type {match_type}")

    winner_token = generate_token(winner_id)
    loser_token = generate_token(loser_id)

    try:
        chest = get_object_or_404(Chest, name=guild_war_chest_name)
        logger.info(f"got on handle_guild_war_match_result chest {chest}")

        winner_data = {"products_id": {chest.item_id: 2}}
        loser_data = {"products_id": {chest.item_id: 1}}

        task_group = group(
            send_to_inventory_service.s(winner_data, winner_token),
            send_to_inventory_service.s(loser_data, loser_token)
        )
        task_group.apply_async()

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@shared_task(bind=True)
def handle_guild_war_game_result(self, event: dict):
    winner_id = event.get("winner_id")
    loser_id = event.get("loser_id")
    event_type = event.get("match_type")

    chest_settings = get_chest_settings()

    guild_war_finish_winner_chest_name = chest_settings.guild_war_winner_chest
    guild_war_finish_loser_chest_name = chest_settings.guild_war_loser_chest

    if event_type != "guild_war":
        return

    guild_members_url = f"{GUILD_API_URL}/api/v1/guild/member/guild_id/"

    try:
        with requests.Session() as s:
            winner = s.get(f"{guild_members_url}{winner_id}")
            loser = s.get(f"{guild_members_url}{loser_id}")

        winner_guild_ids = winner.json().get('value')
        loser_guild_ids = loser.json().get('value')

        chest_for_winner = get_object_or_404(Chest, name=guild_war_finish_winner_chest_name)
        chest_chest_for_loser = get_object_or_404(Chest, name=guild_war_finish_loser_chest_name)

        if loser_guild_ids:
            logger.info(f"Sending {chest_chest_for_loser.name} to {len(loser_guild_ids)} losers")
            with ThreadPoolExecutor() as executor:
                list(executor.map(
                    lambda user_id: send_guild_war_reward(user_id, chest_chest_for_loser.item_id, 1),
                    loser_guild_ids
                ))

        if winner_guild_ids:
            logger.info(f"Sending {chest_for_winner.name} to {len(winner_guild_ids)} winners")
            with ThreadPoolExecutor() as executor:
                list(executor.map(
                    lambda user_id: send_guild_war_reward(user_id, chest_for_winner.item_id, 3),
                    winner_guild_ids
                ))

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
