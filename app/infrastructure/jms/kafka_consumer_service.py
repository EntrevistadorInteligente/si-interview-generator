import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context
from aiokafka.errors import KafkaConnectionError, CommitFailedError

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MAX_RETRIES = 5  # Número máximo de reintentos
RETRY_DELAY = 5  # Tiempo base de espera entre reintentos (en segundos)


class KafkaConsumerService:
    def __init__(self, topic, sasl_username, sasl_password, bootstrap_servers, max_workers=10):
        self.topic = topic
        self.sasl_username = sasl_username
        self.sasl_password = sasl_password
        self.bootstrap_servers = bootstrap_servers
        self.consumer = self.create_consumer()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = True
        self.tasks = []

    def create_consumer(self):
        return AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            sasl_mechanism='SCRAM-SHA-256',
            security_protocol='SASL_SSL',
            sasl_plain_username=self.sasl_username,
            sasl_plain_password=self.sasl_password,
            auto_offset_reset='latest',
            group_id='preparador',
            ssl_context=create_ssl_context(),
            session_timeout_ms=30000,  # 30 segundos
            heartbeat_interval_ms=10000,  # 10 segundos
            max_poll_interval_ms=300000  # 5 minutos
        )

    async def start(self):
        await self.consumer.start()

    async def consume_messages(self, callback):
        retries = 0
        while retries < MAX_RETRIES and self.running:
            try:
                if not self.consumer:
                    await self.start()
                async for msg in self.consumer:
                    if not self.running:
                        break
                    logger.info("Recibiendo mensaje: {}:{:d}:{:d}: key={} value={} timestamp_ms={}".format(
                        msg.topic, msg.partition, msg.offset, msg.key, msg.value, msg.timestamp))
                    # Envía el mensaje a un hilo para procesamiento
                    task = self.executor.submit(self.process_message, msg.value, callback)
                    self.tasks.append(task)
                # Si llegamos aquí, significa que el consumidor se ha cerrado correctamente
                break
            except KafkaConnectionError as e:
                logger.error(f"Error de conexión: {e}. Reintentando en {RETRY_DELAY * (2 ** retries)} segundos...")
                await asyncio.sleep(RETRY_DELAY * (2 ** retries))  # Espera exponencial
                retries += 1
                self.consumer = self.create_consumer()
                await self.start()
            except CommitFailedError as e:
                logger.error(f"Commit fallido: {e}. Esto puede suceder durante una re-asignación del grupo.")
            except Exception as e:
                logger.error(f"Error inesperado: {e}. Reintentando en {RETRY_DELAY * (2 ** retries)} segundos...")
                await asyncio.sleep(RETRY_DELAY * (2 ** retries))  # Espera exponencial
                retries += 1
                self.consumer = self.create_consumer()
                await self.start()
            finally:
                await self.consumer.stop()
        if retries >= MAX_RETRIES:
            logger.error("Número máximo de reintentos alcanzado. Deteniendo consumidor.")
        else:
            logger.info("Consumidor detenido correctamente.")

    async def stop(self):
        self.running = False
        await self.consumer.stop()
        self.executor.shutdown(wait=True)
        # Cancelar todas las tareas pendientes
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

    def process_message(self, message, callback):
        """Función que se ejecuta en el hilo, con su propio event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(callback(message))
            return result
        finally:
            loop.close()
