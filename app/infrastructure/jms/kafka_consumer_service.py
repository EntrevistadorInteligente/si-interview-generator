
from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context


class KafkaConsumerService:
    def __init__(self, topic):
        self.topic = topic
        self.consumer = self.create_consumer()

    def create_consumer(self):
        return AIOKafkaConsumer(self.topic,
                                bootstrap_servers='humble-hornet-11005-us1-kafka.upstash.io:9092',
                                sasl_mechanism='SCRAM-SHA-256',
                                security_protocol='SASL_SSL',
                                sasl_plain_username='aHVtYmxlLWhvcm5ldC0xMTAwNSTUkfJrWsksTN7NbzbgNq7Uenqbl39be2_Jad0',
                                sasl_plain_password='M2MxZjg2NzQtNjVmZS00MmMzLWJjMDAtMjIwYTZiYmI0MzYx',
                                auto_offset_reset='earliest',
                                ssl_context=create_ssl_context())

    async def consume_messages(self, callback):
        await self.consumer.start()
        try:
            async for msg in self.consumer:
                print(
                    "{}:{:d}:{:d}: key={} value={} timestamp_ms={}".format(
                        msg.topic, msg.partition, msg.offset, msg.key, msg.value,
                        msg.timestamp)
                )
                await callback(msg.value)
        finally:
            await self.consumer.stop()


