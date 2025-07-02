from confluent_kafka import Producer, Consumer

KAFKA_BOOTSTRAP_SERVERS = "37.9.53.228:9092"


def get_producer():
	return Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})


def get_consumer(group_id):
	return Consumer({
		'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
		'group.id': group_id,
		'auto.offset.reset': 'earliest'
	})
