from aiokafka import AIOKafkaProducer
import json
import asyncio

from aiokafka.helpers import create_ssl_context


class KafkaProducerService:
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers='humble-hornet-11005-us1-kafka.upstash.io:9092',
            sasl_mechanism='SCRAM-SHA-256',
            security_protocol='SASL_SSL',
            sasl_plain_username='aHVtYmxlLWhvcm5ldC0xMTAwNSTUkfJrWsksTN7NbzbgNq7Uenqbl39be2_Jad0',
            sasl_plain_password='M2MxZjg2NzQtNjVmZS00MmMzLWJjMDAtMjIwYTZiYmI0MzYx',
            ssl_context=create_ssl_context())

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def send_message(self, message: dict, topic):
        await self.producer.start()
        await self.producer.send_and_wait(
            topic,
            json.dumps(message).encode('utf-8')
        )
