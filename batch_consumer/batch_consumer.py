import json
import os

import pika
from pymongo import MongoClient

# Configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb:27017/")

# Setup MongoDB client & collection
mongo = MongoClient(MONGO_URL)
db = mongo["air_quality"]
latest = db["latest_pm25"]

# Setup RabbitMQ connection & exchange/queue
conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
ch = conn.channel()
ch.exchange_declare(exchange="raw_data", exchange_type="fanout", durable=True)
queue_name = ch.queue_declare(queue="batch_queue", durable=True).method.queue
ch.queue_bind(exchange="raw_data", queue=queue_name)


def callback(ch, method, properties, body):
    rec = json.loads(body)
    lat = rec.get("lat")
    lon = rec.get("lon")
    # Skip if no lat/lon
    if lat is None or lon is None:
        return ch.basic_ack(delivery_tag=method.delivery_tag)

    key = {"lat": lat, "lon": lon}
    update = {
        "$set": {
            "lat": lat,
            "lon": lon,
            "pm25": rec.get("pm25"),
            "unit": rec.get("unit"),
            "timestamp": rec.get("timestamp"),
        }
    }
    latest.update_one(key, update, upsert=True)
    ch.basic_ack(delivery_tag=method.delivery_tag)


ch.basic_qos(prefetch_count=20)
ch.basic_consume(queue=queue_name, on_message_callback=callback)
print(f"[Batch] Consumer started on queue '{queue_name}'")
ch.start_consuming()
