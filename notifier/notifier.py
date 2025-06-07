import json
import os
from datetime import datetime

import pika
from pymongo import MongoClient, ASCENDING

# Configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb:27017/")

# MongoDB setup
mongo = MongoClient(MONGO_URL)
db = mongo["air_quality"]
alerts = db["alerts"]

# Create indexes
alerts.create_index([("timestamp", ASCENDING)])
alerts.create_index([("severity", ASCENDING)])
alerts.create_index([("lat", ASCENDING), ("lon", ASCENDING)])

# RabbitMQ setup
conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
ch = conn.channel()
ch.exchange_declare(exchange="alerts", exchange_type="fanout", durable=True)
queue = ch.queue_declare(queue="notify_queue", durable=True).method.queue
ch.queue_bind(exchange="alerts", queue=queue)

def format_alert_message(alert):
    """Format alert message based on severity."""
    severity_colors = {
        "info": "🔵",
        "warning": "🟡",
        "alert": "🟠",
        "critical": "🔴"
    }
    emoji = severity_colors.get(alert["severity"], "⚪")
    return (
        f"{emoji} {alert['severity'].upper()} ALERT\n"
        f"PM2.5: {alert['pm25']} {alert['unit']}\n"
        f"Location: {alert['lat']}, {alert['lon']}\n"
        f"Threshold: {alert['threshold']} {alert['unit']}\n"
        f"Description: {alert['description']}\n"
        f"Time: {alert['timestamp']}"
    )

def callback(ch, method, properties, body):
    alert = json.loads(body)
    
    # Add acknowledgment status
    alert["acknowledged"] = False
    alert["acknowledged_at"] = None
    alert["acknowledged_by"] = None
    
    # Store in MongoDB
    alerts.insert_one(alert)
    
    # Print formatted message
    print(format_alert_message(alert))
    
    # TODO: Send notifications based on severity
    # - Email for critical alerts
    # - SMS for critical alerts
    # - Web push for all alerts
    
    ch.basic_ack(delivery_tag=method.delivery_tag)


# Start consuming alerts
ch.basic_consume(queue=queue, on_message_callback=callback)
print("[Notifier] Service started with alert persistence")

ch.start_consuming()
