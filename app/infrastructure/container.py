import os

from dependency_injector import containers, providers
from dotenv import load_dotenv

from app.application.services.generar_feedback_service import GenerarFeedbackService
from app.application.services.obtener_contextos_rags_service import ObtenerContextosRags
from app.application.services.generar_modelo_service import GenerarModeloContextoPdf
from app.infrastructure.jms.kafka_consumer_service import KafkaConsumerService
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.application.services.generar_entrevista_service import GenerarEntrevistaService
from app.infrastructure.handlers import Handlers
from app.infrastructure.jms import Jms
from app.infrastructure.repositories.hoja_de_vida_rag import HojaDeVidaMongoRepository
from app.infrastructure.repositories.informacion_empresa_rag import InformacionEmpresaMongoRepository
from app.infrastructure.repositories.preparador_entrevista_rag import PreparacionEntrevistaMongoRepository
from app.infrastructure.repositories.worker_manager import WorkerManagerRepository

# Carga las variables de entorno al inicio
load_dotenv()


class Container(containers.DeclarativeContainer):
    # loads all handlers where @injects are set
    wiring_config = containers.WiringConfiguration(modules=Handlers.modules())
    wiring_config2 = containers.WiringConfiguration(modules=Jms.modules())

    # Repositories
    # Obtener la URL de MongoDB desde las variables de entorno
    MONGO_URL = os.getenv('MONGO_URI')
    sasl_username_kafka = os.getenv('KAFKA_UPSTAR_USER')
    sasl_password_kafka = os.getenv('KAFKA_UPSTAR_PASSWORD')
    bootstrap_servers_kafka = os.getenv('KAFKA_UPSTAR_SERVER_URL')

    # MONGO_URI no esté definida
    if MONGO_URL is None:
        raise ValueError("MONGO_URI environment variable is not set.")

    hoja_de_vida_repository = providers.Factory(
        HojaDeVidaMongoRepository,
        mongo_url=MONGO_URL
    )
    informacion_empresa_repository = providers.Factory(
        InformacionEmpresaMongoRepository,
        mongo_url=MONGO_URL
    )
    worker_manager_repository = providers.Factory(
        WorkerManagerRepository,
        mongo_url=MONGO_URL
    )
    preparacion_entrevista_repository = providers.Factory(
        PreparacionEntrevistaMongoRepository,
        mongo_url=MONGO_URL
    )

    # Dependencias
    generar_modelo_servicio = providers.Factory(
        GenerarModeloContextoPdf,
        preparacion_entrevista_repository=preparacion_entrevista_repository)

    # Servicio que depende de las anteriores
    obtener_contextos_rags_service = providers.Factory(
        ObtenerContextosRags,
        hoja_de_vida_repository=hoja_de_vida_repository,
        informacion_empresa_repository=informacion_empresa_repository
    )

    kafka_consumer_service = providers.Factory(
        KafkaConsumerService
    )

    kafka_producer_service = providers.Factory(
        KafkaProducerService,
        sasl_username=sasl_username_kafka,
        sasl_password=sasl_password_kafka,
        bootstrap_servers=bootstrap_servers_kafka
    )

    # Servicio que depende de las anteriores
    generar_entrevista_service = providers.Factory(
        GenerarEntrevistaService,
        obtener_contextos_rags_service=obtener_contextos_rags_service,
        generar_modelo_servicio=generar_modelo_servicio,
        hoja_de_vida_repository=hoja_de_vida_repository,
        informacion_empresa_repository=informacion_empresa_repository,
        preparacion_entrevista_repository=preparacion_entrevista_repository,
        kafka_producer_service=kafka_producer_service,
        worker_manager_repository=worker_manager_repository
    )

    generar_feedback_service = providers.Factory(
        GenerarFeedbackService,
        obtener_contextos_rags_service=obtener_contextos_rags_service,
        generar_modelo_servicio=generar_modelo_servicio,
        preparacion_entrevista_repository=preparacion_entrevista_repository,
        kafka_producer_service=kafka_producer_service,
        worker_manager_repository=worker_manager_repository
    )

    procesar_peticion_entrevista_message = providers.Factory(
        # Pasa las dependencias requeridas por procesar_peticion_entrevista_message aquí, como:
        generar_entrevista_service=generar_entrevista_service
    )

