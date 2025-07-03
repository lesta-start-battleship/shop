from confluent_kafka import Producer, Consumer

from config.settings import env


KAFKA_BOOTSTRAP_SERVERS = env("KAFKA_BOOTSTRAP_SERVERS")


def get_producer():
	return Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})


def get_consumer(group_id):
	return Consumer({
		'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
		'group.id': group_id,
		'auto.offset.reset': 'earliest'
	})
