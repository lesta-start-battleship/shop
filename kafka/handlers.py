import logging

logger = logging.getLogger(__name__)


def handle_guild_war_game(event: dict):
    # TODO
    """
    test_hanlder
    """
    user = event.get("user_id")
    place = event.get("place")

    if not all([user, place]):
        logger.error(f"{event}")
        return

    logger.info(f"[Kafka]  guild war game win {user} place -> {place}")