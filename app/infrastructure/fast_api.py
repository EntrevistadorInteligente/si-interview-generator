import asyncio
from fastapi import FastAPI
from app.infrastructure.jms.kafka_consumer_service import KafkaConsumerService
from app.infrastructure.jms.kafka_feedback_consumer_service import KafkaFeedbackConsumerService
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.infrastructure.container import Container
from app.infrastructure.handlers import Handlers
from app.infrastructure.handlers.listener import procesar_peticion_entrevista_message, \
    procesar_peticion_feedback_message

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
        kafka_feedback_consumer_service = KafkaFeedbackConsumerService('feedbackPublisherTopic')
        global kafka_producer_service
        kafka_producer_service = KafkaProducerService('localhost:9092')

        # Iniciar el servicio del productor Kafka.
        await kafka_producer_service.start()

        # Crear tareas para los consumidores de manera que no bloqueen el inicio de uno a otro.
        task2 = asyncio.create_task(kafka_consumer_service.consume_messages(procesar_peticion_entrevista_message))
        task1 = asyncio.create_task(kafka_feedback_consumer_service.
                                    consume_messages(procesar_peticion_feedback_message))

        # Opcional: Esperar a que ambas tareas estén corriendo si es necesario aquí.
        await asyncio.gather(task1, task2)

    return fast_api
