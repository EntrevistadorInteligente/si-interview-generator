from aiokafka import AIOKafkaConsumer


class KafkaConsumerService:
    def __init__(self, topic):
        self.topic = topic
        self.consumer = self.create_consumer()

    def create_consumer(self):
        conf = {
            # Configuración de tu consumidor Kafka.
        }
        return AIOKafkaConsumer(self.topic, **conf)

    async def consume_messages(self, callback):
        await self.consumer.start()
        try:
            async for message in self.consumer:
                await callback(message)
        finally:
            await self.consumer.stop()


