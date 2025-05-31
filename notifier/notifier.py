import json

import pika

RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"
conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
ch = conn.channel()
ch.exchange_declare(exchange="alerts", exchange_type="fanout", durable=True)
queue = ch.queue_declare(queue="notify_queue", durable=True).method.queue
ch.queue_bind(exchange="alerts", queue=queue)


def callback(ch, method, properties, body):
    alert = json.loads(body)
    # TODO: integrate SMTP or SMS API
    print(f"[Notifier] Alert: {alert}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


ch.basic_consume(queue=queue, on_message_callback=callback)
print("[Notifier] Service started")
ch.start_consuming()
