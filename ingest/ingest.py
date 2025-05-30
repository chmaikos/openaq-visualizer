import time
import json
import requests
import pika

API_URL = 'https://api.openaq.org/v2/latest?limit=100'
RABBITMQ_URL = 'amqp://guest:guest@rabbitmq:5672/'

connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
channel = connection.channel()
channel.exchange_declare(exchange='raw_data', exchange_type='fanout', durable=True)

while True:
    resp = requests.get(API_URL, timeout=10)
    data = resp.json().get('results', [])
    for record in data:
        channel.basic_publish(
            exchange='raw_data', routing_key='', body=json.dumps(record),
            properties=pika.BasicProperties(content_type='application/json', delivery_mode=2)
        )
    print(f"[Ingest] Published {len(data)} records")
    time.sleep(60)