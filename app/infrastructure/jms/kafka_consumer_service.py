import logging

from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class KafkaConsumerService:
    def __init__(self, topic, sasl_username, sasl_password, bootstrap_servers):
        self.topic = topic
        self.sasl_username = sasl_username
        self.sasl_password = sasl_password
        self.bootstrap_servers = bootstrap_servers
        self.consumer = self.create_consumer()

    def create_consumer(self):
        return AIOKafkaConsumer(self.topic,
                                bootstrap_servers=self.bootstrap_servers,
                                sasl_mechanism='SCRAM-SHA-256',
                                security_protocol='SASL_SSL',
                                sasl_plain_username=self.sasl_username,
                                sasl_plain_password=self.sasl_password,
                                auto_offset_reset='earliest',
                                ssl_context=create_ssl_context())

    async def consume_messages(self, callback):
        await self.consumer.start()
        try:
            async for msg in self.consumer:
                logger.info("Recibiendo mensaje : {}:{:d}:{:d}: key={} value={} timestamp_ms={}".format(
                    msg.topic, msg.partition, msg.offset, msg.key, msg.value, msg.timestamp))
                await callback(msg.value)
        finally:
            logger.info("Cerrando")
            await self.consumer.stop()


