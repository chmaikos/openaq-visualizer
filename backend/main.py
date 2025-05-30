from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from pymongo import MongoClient
import asyncio
import json
import pika

app = FastAPI()

mongo = MongoClient('mongodb://mongodb:27017/')
db = mongo['air_quality']
measurements = db['measurements']

RABBITMQ_URL = 'amqp://guest:guest@rabbitmq:5672/'

class RMQConsumer:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='alerts', exchange_type='fanout', durable=True)
        self.queue = self.channel.queue_declare(queue='', exclusive=True).method.queue
        self.channel.queue_bind(exchange='alerts', queue=self.queue)

    def consume(self, callback):
        for method, properties, body in self.channel.consume(self.queue, inactivity_timeout=1):
            if body:
                callback(json.loads(body))

consumer = RMQConsumer()
subscribers = []

@app.on_event("startup")
async def startup_background():
    loop = asyncio.get_event_loop()
    def push_alert(alert):
        for ws in subscribers:
            asyncio.run_coroutine_threadsafe(ws.send_json(alert), loop)
    while True:
        consumer.consume(push_alert)
        await asyncio.sleep(0.1)

@app.get("/api/history/{city}")
def get_history(city: str):
    docs = list(measurements.find({'city': city}).sort('date', -1).limit(100))
    if not docs:
        raise HTTPException(status_code=404, detail="No data")
    return JSONResponse(docs)

@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    await ws.accept()
    subscribers.append(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        subscribers.remove(ws)