import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class KafkaConsumerService:
    def __init__(self, topic, sasl_username, sasl_password, bootstrap_servers, max_workers=10):
        self.topic = topic
        self.sasl_username = sasl_username
        self.sasl_password = sasl_password
        self.bootstrap_servers = bootstrap_servers
        self.consumer = self.create_consumer()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def create_consumer(self):
        return AIOKafkaConsumer(self.topic,
                                bootstrap_servers=self.bootstrap_servers,
                                sasl_mechanism='SCRAM-SHA-256',
                                security_protocol='SASL_SSL',
                                sasl_plain_username=self.sasl_username,
                                sasl_plain_password=self.sasl_password,
                                auto_offset_reset='latest',
                                group_id='preparador',
                                ssl_context=create_ssl_context())

    async def start(self):
        await self.consumer.start()

    async def consume_messages(self, callback):
        try:
            async for msg in self.consumer:
                logger.info("Recibiendo mensaje : {}:{:d}:{:d}: key={} value={} timestamp_ms={}".format(
                    msg.topic, msg.partition, msg.offset, msg.key, msg.value, msg.timestamp))
                # Envía el mensaje a un hilo para procesamiento
                self.executor.submit(self.process_message, msg.value, callback)
        finally:
            logger.info("Cerrando")
            await self.consumer.stop()

    def process_message(self, message, callback):
        """Función que se ejecuta en el hilo, con su propio event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(callback(message))
            return result
        finally:
            loop.close()


