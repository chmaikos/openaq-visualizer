import json
import pika

THRESHOLDS = {'pm25': 35}
RABBITMQ_URL = 'amqp://guest:guest@rabbitmq:5672/'
conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
ch = conn.channel()
ch.exchange_declare(exchange='raw_data', exchange_type='fanout', durable=True)
ch.exchange_declare(exchange='alerts', exchange_type='fanout', durable=True)
queue = ch.queue_declare(queue='speed_queue', durable=True).method.queue
ch.queue_bind(exchange='raw_data', queue=queue)


def callback(ch, method, properties, body):
    rec = json.loads(body)
    for m in rec.get('measurements', []):
        if m['parameter'] in THRESHOLDS and m['value'] > THRESHOLDS[m['parameter']]:
            alert = {
                'city': rec['city'],
                'location': rec['location'],
                'parameter': m['parameter'],
                'value': m['value'],
                'unit': m['unit'],
                'timestamp': m['lastUpdated']
            }
            ch.basic_publish(
                exchange='alerts', routing_key='', body=json.dumps(alert),
                properties=pika.BasicProperties(content_type='application/json', delivery_mode=2)
            )
    ch.basic_ack(delivery_tag=method.delivery_tag)

ch.basic_qos(prefetch_count=10)
ch.basic_consume(queue=queue, on_message_callback=callback)
print('[Speed] Processor started')
ch.start_consuming()