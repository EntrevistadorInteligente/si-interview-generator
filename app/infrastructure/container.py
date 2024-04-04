from dependency_injector import containers, providers
from app.application.services.obtener_contextos_rags_service import ObtenerContextosRags
from app.application.services.generar_modelo_contexto_pdf import GenerarModeloContextoPdf
from app.infrastructure.jms.kafka_consumer_service import KafkaConsumerService
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.application.services.generar_entrevista_service import GenerarEntrevistaService
from app.infrastructure.handlers import Handlers
from app.infrastructure.jms import Jms
from app.infrastructure.repositories.hoja_de_vida_rag import HojaDeVidaMongoRepository
from app.infrastructure.repositories.informacion_empresa_rag import InformacionEmpresaMongoRepository


class Container(containers.DeclarativeContainer):
    # loads all handlers where @injects are set
    wiring_config = containers.WiringConfiguration(modules=Handlers.modules())
    wiring_config2 = containers.WiringConfiguration(modules=Jms.modules())

    # Dependencias
    generar_modelo_contexto_pdf = providers.Factory(GenerarModeloContextoPdf)

    # Repositories
    hoja_de_vida_repository = providers.Singleton(HojaDeVidaMongoRepository)
    informacion_empresa_repository = providers.Singleton(InformacionEmpresaMongoRepository)

    # Servicio que depende de las anteriores
    obtener_contextos_rags_service = providers.Factory(
        ObtenerContextosRags,
        hoja_de_vida_repository=hoja_de_vida_repository,
        informacion_empresa_repository=informacion_empresa_repository
    )

    # Servicio que depende de las anteriores
    generar_entrevista_service = providers.Factory(
        GenerarEntrevistaService,
        obtener_contextos_rags_service=obtener_contextos_rags_service,
        generar_modelo_contexto_pdf=generar_modelo_contexto_pdf
    )

    procesar_peticion_entrevista_message = providers.Factory(
        # Pasa las dependencias requeridas por procesar_peticion_entrevista_message aquí, como:
        generar_entrevista_service=generar_entrevista_service
    )

    kafka_consumer_service = providers.Singleton(
        KafkaConsumerService,
        topic='generadorPublisherTopic',
    )

    kafka_producer_service = providers.Singleton(
        KafkaProducerService,
        bootstrap_servers='localhost:9092',
        topic='hojaDeVidaListenerTopic',
    )
