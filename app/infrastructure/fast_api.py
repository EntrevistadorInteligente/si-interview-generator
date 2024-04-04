import asyncio
from fastapi import FastAPI
from app.infrastructure.jms.kafka_consumer_service import KafkaConsumerService
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.infrastructure.container import Container
from app.infrastructure.handlers import Handlers
from app.infrastructure.handlers.listener import procesar_peticion_entrevista_message

kafka_producer_service = None


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

    @fast_api.on_event("startup")
    async def startup_event():
        kafka_consumer_service = KafkaConsumerService('generadorPublisherTopic')
        # Registramos la tarea del consumidor para ejecutarse como una tarea de fondo.
        await asyncio.create_task(kafka_consumer_service.consume_messages(procesar_peticion_entrevista_message))

        global kafka_producer_service
        kafka_producer_service = KafkaProducerService('localhost:9092', 'hojaDeVidaListenerTopic')
        await kafka_producer_service.start()
    return fast_api
