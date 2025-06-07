import json
import os
import time
from datetime import datetime

import paho.mqtt.client as mqtt
import pika

from config import PM25Thresholds, SeverityLevel

# Configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# Set up RabbitMQ connection
conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
ch = conn.channel()
ch.exchange_declare(exchange="raw_data", exchange_type="fanout", durable=True)
# queue raw_data
queue_name = ch.queue_declare(queue="speed_queue", durable=True).method.queue
ch.queue_bind(exchange="raw_data", queue=queue_name)

# Set up MQTT client
mqtt_client = mqtt.Client()
try:
    mqtt_client.connect(host=MQTT_BROKER, port=MQTT_PORT)
    print(f"[Speed] Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
except Exception as e:
    print(f"[Speed] Error connecting to MQTT broker: {e}")
    # Retry connection after a delay
    time.sleep(5)
    mqtt_client.connect(host=MQTT_BROKER, port=MQTT_PORT)

def callback(ch, method, properties, body):
    try:
        rec = json.loads(body)
        val = rec.get("pm25") or 0
        
        # Get threshold configuration for this value
        threshold = PM25Thresholds.get_threshold_for_value(val)
        
        if threshold:
            alert = {
                "lat": rec.get("lat"),
                "lon": rec.get("lon"),
                "pm25": val,
                "unit": rec.get("unit"),
                "timestamp": rec.get("timestamp") or datetime.utcnow().isoformat(),
                "severity": threshold.severity,
                "threshold": threshold.value,
                "description": threshold.description
            }
            
            # RabbitMQ alerts
            ch.basic_publish(
                exchange="alerts",
                routing_key="",
                body=json.dumps(alert),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2
                ),
            )
            
            # MQTT topic "alerts"
            mqtt_client.publish("alerts", json.dumps(alert))
            print(f"[Speed] Alert published: {alert}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[Speed] Error processing message: {e}")
        # Don't ack the message so it can be retried
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

ch.exchange_declare(exchange="alerts", exchange_type="fanout", durable=True)

ch.basic_qos(prefetch_count=20)
ch.basic_consume(queue=queue_name, on_message_callback=callback)
print("[Speed] Processor started with configurable thresholds")

# MQTT network loop on separate thread
mqtt_client.loop_start()

try:
    ch.start_consuming()
except KeyboardInterrupt:
    print("[Speed] Shutting down...")
finally:  # Clean up
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    conn.close()
