import json
import os
import time

import pika
import requests

# Configuration
API_URL = "https://api.openaq.org/v3/parameters/2/latest?limit=1000"
API_KEY = os.getenv(
    "OPENAQ_API_KEY", "e6ced4ecbbd6cf9f67c9472d3e1c969ace75290d525fe3bbdd9dfdafe9e5f8d0"
)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

# Setup RabbitMQ connection & exchange
connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
channel = connection.channel()
channel.exchange_declare(exchange="raw_data", exchange_type="fanout", durable=True)

while True:
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    try:
        resp = requests.get(API_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except Exception as e:
        print(f"[Ingest] Error fetching data: {e}")
        time.sleep(60)
        continue

    count = 0
    for item in results:
        coords = item.get("coordinates") or {}
        lat = coords.get("latitude")
        lon = coords.get("longitude")
        # Ignore if no coordinates
        if lat is None or lon is None:
            continue

        record = {
            "lat": lat,
            "lon": lon,
            "pm25": item.get("value"),
            "unit": item.get("unit"),
            "timestamp": item.get("date", {}).get("utc"),
        }
        channel.basic_publish(
            exchange="raw_data",
            routing_key="",
            body=json.dumps(record),
            properties=pika.BasicProperties(
                content_type="application/json", delivery_mode=2
            ),
        )
        count += 1

    print(f"[Ingest] Published {count} PM2.5 records")
    time.sleep(60)
