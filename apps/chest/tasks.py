import json
import logging
from concurrent.futures import ThreadPoolExecutor

import requests
from celery import shared_task, group
from rest_framework.generics import get_object_or_404

from apps.chest.models import Chest
from apps.chest.utils import open_chest, generate_token, send_guild_war_reward
from apps.saga.saga_orchestrator import get_producer
from config import settings

logger = logging.getLogger(__name__)

INVENTORY_API_URL = settings.INVENTORY_SERVICE_URL
AUTH_API_URL = settings.AUTH_SERVICE_URL
GUILD_API_URL = settings.GUILD_API_URL


@shared_task(bind=True, max_retries=3)
def open_chest_task(self, chest_id: int, token, user_id, callback_url, amount: int = 1, ):
    logger.info("Open chest celery task started")

    try:
        # Headers with received token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Open chest in inventory
        open_chest_url = f"{INVENTORY_API_URL}/inventory/use_item/"
        open_response = requests.patch(
            open_chest_url,
            json={
                "item_id": chest_id,
                "amount": amount
            },
            headers=headers
        )

        if open_response.status_code == 422:
            raise Exception("Validation Error")
        elif open_response.status_code != 200:
            raise Exception("Inventory service error")

        # Open claimed chests
        chest = Chest.objects.filter(item_id=chest_id).prefetch_related('product').first()

        rewards = open_chest(chest, amount)
        chests = rewards["promo_chests"]

        distribute_chest_opening_result(rewards, token)
        if chests:
            send_chest_event_to_kafka.delay(chests, user_id)

        if callback_url:
            send_callback.delay(rewards, callback_url, token)

    except Exception as e:
        logger.error(f"Error in open_chest_task: {str(e)}")
        self.retry(exc=e, countdown=30)


@shared_task(bind=True, max_retries=3)
def send_to_inventory_service(self, result_data, token):
    """Celery task for send result about items to inventory"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    inventory_response_url = f"{INVENTORY_API_URL}/inventory/add_item/"

    for item_id, amount in result_data["products_id"].items():
        try:
            requests.patch(
                inventory_response_url,
                json={
                    "item_id": item_id,
                    "amount": amount
                },
                headers=headers
            )
        except Exception as e:
            logger.error(f"Error sending item {item_id} to inventory: {str(e)}")
            self.retry(exc=e, countdown=10)


@shared_task(bind=True, max_retries=3)
def send_to_user_service(self, result_data, token):
    """Celery task for send result about gold to user"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    inventory_response_url = f"{AUTH_API_URL}/api/v1/currencies/"
    try:
        gold = result_data.get("gold", 0)
        if gold > 0:
            requests.patch(
                inventory_response_url,
                json={
                    "gold": gold
                },
                headers=headers
            )
    except Exception as e:
        logger.error(f"Error sending gold to user service: {str(e)}")
        self.retry(exc=e, countdown=10)


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


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def send_chest_event_to_kafka(self, chests, user_id):
    """Send chests open event to scoreboard Kafka"""
    try:
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
        return True
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@shared_task(bind=True)
def handle_guild_war_match_result(self, event: dict):
    winner_id = event.get("winner_id")
    loser_id = event.get("loser_id")
    match_type = event.get("match_type")
    guild_war_chest_name = "guild_war"

    logger.info(f"winner {winner_id}, loser {loser_id}, match_type {match_type}")

    winner_token = generate_token(winner_id)
    loser_token = generate_token(loser_id)

    try:
        if match_type == "guild_war_match":
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
    event_type = event.get("event")

    guild_war_finish_winner_chest_name = "guild_war_finish_winner"
    guild_war_finish_loser_chest_name = "guild_war_finish_loser"

    if event_type != "guild_war":
        return

    guild_members_url = f"{GUILD_API_URL}/api/v1/guild/member/"

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
