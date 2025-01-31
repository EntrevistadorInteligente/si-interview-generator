import asyncio
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.infrastructure.jms.kafka_consumer_service import KafkaConsumerService
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.infrastructure.container import Container
from app.infrastructure.handlers import Handlers
from app.infrastructure.handlers.listener import procesar_peticion_entrevista_message, \
    procesar_peticion_feedback_message

kafka_producer_service = None
load_dotenv()


def create_app():
    fast_api = FastAPI()
    fast_api.container = Container()
    for handler in Handlers.iterator():
        fast_api.include_router(handler.router)

    @fast_api.on_event("shutdown")
    async def shutdown_event():
        global kafka_producer_service
        if kafka_producer_service:
            await kafka_producer_service.stop()
            print("Kafka producer service stopped")

    @fast_api.on_event("startup")
    async def startup_event():
        sasl_username_kafka = os.getenv('KAFKA_UPSTAR_USER')
        sasl_password_kafka = os.getenv('KAFKA_UPSTAR_PASSWORD')
        bootstrap_servers_kafka = os.getenv('KAFKA_SERVER')

        kafka_consumer_service = KafkaConsumerService('generadorPublisherTopic',
                                                      sasl_username_kafka,
                                                      sasl_password_kafka,
                                                      bootstrap_servers_kafka)
        kafka_feedback_consumer_service = KafkaConsumerService('feedbackPublisherTopic',
                                                               sasl_username_kafka,
                                                               sasl_password_kafka,
                                                               bootstrap_servers_kafka)

        global kafka_producer_service
        kafka_producer_service = KafkaProducerService(sasl_username_kafka,
                                                      sasl_password_kafka,
                                                      bootstrap_servers_kafka)

        await kafka_producer_service.start()
        print("Kafka producer service started")

        # Iniciar consumidores de Kafka en tareas asincrónicas separadas
        asyncio.create_task(kafka_consumer_service.start())
        asyncio.create_task(kafka_feedback_consumer_service.start())
        asyncio.create_task(kafka_consumer_service.consume_messages(procesar_peticion_entrevista_message))
        asyncio.create_task(kafka_feedback_consumer_service.consume_messages(procesar_peticion_feedback_message))

        print("Kafka consumer services started")

    return fast_api


application = create_app()
