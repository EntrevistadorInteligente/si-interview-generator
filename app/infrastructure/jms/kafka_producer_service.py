from aiokafka import AIOKafkaProducer
import json
import asyncio


class KafkaProducerService:
    def __init__(self, bootstrap_servers, topic):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def send_message(self, message: dict):
        await self.producer.start()
        await self.producer.send_and_wait(
            self.topic,
            json.dumps(message).encode('utf-8')
        )
