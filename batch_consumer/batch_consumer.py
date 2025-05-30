import json
import pika
from pymongo import MongoClient

# MongoDB setup
mongo = MongoClient('mongodb://mongodb:27017/')
db = mongo['air_quality']
measurements = db['measurements']

# RabbitMQ setup
RABBITMQ_URL = 'amqp://guest:guest@rabbitmq:5672/'
conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
ch = conn.channel()
ch.exchange_declare(exchange='raw_data', exchange_type='fanout', durable=True)
queue = ch.queue_declare(queue='batch_queue', durable=True).method.queue
ch.queue_bind(exchange='raw_data', queue=queue)


def callback(ch, method, properties, body):
    rec = json.loads(body)
    measurements.insert_one({
        'city': rec['city'],
        'location': rec['location'],
        'date': rec['measurements'][0]['lastUpdated'].split('T')[0],
        'records': rec.get('measurements', [])
    })
    ch.basic_ack(delivery_tag=method.delivery_tag)

ch.basic_qos(prefetch_count=10)
ch.basic_consume(queue=queue, on_message_callback=callback)
print('[Batch] Consumer started')
ch.start_consuming()