import json
import os
import time

import paho.mqtt.client as mqtt
import pika

# Configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
MQTT_URL = os.getenv("MQTT_URL", "tcp://mosquitto:1883")
THRESHOLD_PM25 = float(os.getenv("THRESHOLD_PM25", "15"))

# Set up RabbitMQ connection
conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
ch = conn.channel()
ch.exchange_declare(exchange="raw_data", exchange_type="fanout", durable=True)
# Δηλώνουμε queue και την bind-άρουμε στο raw_data
queue_name = ch.queue_declare(queue="speed_queue", durable=True).method.queue
ch.queue_bind(exchange="raw_data", queue=queue_name)

# Set up MQTT client (paho) για δημοσίευση σε topic "alerts"
mqtt_client = mqtt.Client()
# Αν χρειαζόμαστε authentication: mqtt_client.username_pw_set(user, pass)
mqtt_client.connect(host="mosquitto", port=1883)  # εντός Docker δίκτυο


def callback(ch, method, properties, body):
    rec = json.loads(body)
    val = rec.get("pm25") or 0
    if val > THRESHOLD_PM25:
        alert = {
            "lat": rec.get("lat"),
            "lon": rec.get("lon"),
            "pm25": val,
            "unit": rec.get("unit"),
            "timestamp": rec.get("timestamp"),
        }
        # 1) Δημοσίευση σε RabbitMQ alerts (προαιρετικό)
        ch.basic_publish(
            exchange="alerts",
            routing_key="",
            body=json.dumps(alert),
            properties=pika.BasicProperties(
                content_type="application/json", delivery_mode=2
            ),
        )
        # 2) Δημοσίευση στο MQTT topic "alerts"
        mqtt_client.publish("alerts", json.dumps(alert))
        print(f"[Speed] Alert published: {alert}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


# Δημιουργία exchange 'alerts' (αν θέλουμε να το χρησιμοποιήσουμε)
ch.exchange_declare(exchange="alerts", exchange_type="fanout", durable=True)

ch.basic_qos(prefetch_count=20)
ch.basic_consume(queue=queue_name, on_message_callback=callback)
print(f"[Speed] Processor started – threshold PM2.5 > {THRESHOLD_PM25} µg/m³")

# Πρέπει να τρέχει το MQTT network loop σε ξεχωριστό thread
mqtt_client.loop_start()

try:
    ch.start_consuming()
finally:
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    conn.close()
