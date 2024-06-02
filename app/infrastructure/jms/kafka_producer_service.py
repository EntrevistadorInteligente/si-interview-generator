import logging

from aiokafka import AIOKafkaProducer
import json

from aiokafka.helpers import create_ssl_context

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class KafkaProducerService:
    def __init__(self, sasl_username, sasl_password, bootstrap_servers):
        self.sasl_username = sasl_username
        self.sasl_password = sasl_password
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        if not self.producer:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                sasl_mechanism='SCRAM-SHA-256',
                security_protocol='SASL_SSL',
                sasl_plain_username=self.sasl_username,
                sasl_plain_password=self.sasl_password,
                ssl_context=create_ssl_context())
            await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            self.producer = None

    async def send_message(self, message: dict, topic):
        if not self.producer:
            await self.start()
        logger.info(f"Enviando mensaje a: topic={topic}, tamaño message={len(json.dumps(message))}")
        await self.producer.send_and_wait(
            topic,
            json.dumps(message).encode('utf-8')
        )
        logger.info("Mensaje enviado")
