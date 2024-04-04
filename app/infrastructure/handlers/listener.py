from fastapi import Depends, APIRouter

from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.application.services.generar_entrevista_service import GenerarEntrevistaService
from app.infrastructure.container import Container
from dependency_injector.wiring import Provide, inject
import json
from app.infrastructure.schemas.hoja_de_vida_dto import (SolicitudGeneracionEntrevistaDto,
                                                         ProcesoEntrevistaDto, EstadoProcesoEnum)

router = APIRouter(
    prefix='/analizador2',
    tags=['analizador']
)


@router.get('/', response_model=str)
@inject
async def procesar_peticion_entrevista_message(
        message,generar_entrevista_service: GenerarEntrevistaService =
        Depends(Provide[Container.generar_entrevista_service]),
        kafka_producer_service: KafkaProducerService =
        Depends(Provide[Container.kafka_producer_service])):

    data = json.loads(message.value.decode('utf-8'))
    id_entrevista = data.get('id_entrevista')
    preparacion_entrevista_dto = SolicitudGeneracionEntrevistaDto(
        id_entrevista=id_entrevista,
        id_hoja_de_vida=data.get('id_hoja_de_vida'),
        id_informacion_empresa=data.get('id_informacion_empresa')
    )
    hoja_de_vida_dto = await generar_entrevista_service.ejecutar(preparacion_entrevista_dto)

    proceso_entrevista = ProcesoEntrevistaDto(
        uuid=preparacion_entrevista_dto.id_entrevista,
        estado=EstadoProcesoEnum.FN,
        fuente="ANALIZADOR"
    )

    await kafka_producer_service.send_message({
        "proceso_entrevista": proceso_entrevista.dict(),
        "id_entrevista": id_entrevista,
        "hoja_de_vida": hoja_de_vida_dto.dict()})



