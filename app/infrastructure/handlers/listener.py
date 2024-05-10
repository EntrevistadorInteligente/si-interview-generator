import logging

from fastapi import Depends, APIRouter

from app.application.services.generar_feedback_service import GenerarFeedbackService
from app.application.services.generar_entrevista_service import GenerarEntrevistaService
from app.infrastructure.container import Container
from dependency_injector.wiring import Provide, inject
import json
from app.infrastructure.schemas.hoja_de_vida_dto import (SolicitudGeneracionEntrevistaDto, PreguntasDto)


# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix='/analizador2',
    tags=['analizador']
)


@router.get('/', response_model=str)
@inject
async def procesar_peticion_entrevista_message(
        message,
        generar_entrevista_service: GenerarEntrevistaService = Depends(Provide[Container.generar_entrevista_service])):
    try:
        data = json.loads(message.decode('utf-8'))
        preparacion_entrevista_dto = SolicitudGeneracionEntrevistaDto(
            id_entrevista=data.get('id_entrevista'),
            id_hoja_de_vida=data.get('id_hoja_de_vida'),
            id_informacion_empresa=data.get('id_informacion_empresa')
        )
        # Procesar y loguear a la cola
        await generar_entrevista_service.ejecutar(preparacion_entrevista_dto)
        logger.info(f"Procesamiento completado para la entrevista ID {data.get('id_entrevista')}.")

    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}. Mensaje recibido: {message}")
    except Exception as e:
        logger.error(f"Error inesperado durante el procesamiento de la entrevista: {e}")


@router.get('/2', response_model=str)
@inject
async def procesar_peticion_feedback_message(
        message, generar_feedback_service: GenerarFeedbackService =
        Depends(Provide[Container.generar_feedback_service])):
    try:
        data = json.loads(message.decode('utf-8'))
        await generar_feedback_service.ejecutar(PreguntasDto(**data))
        logger.info(f"Procesamiento de feedback completado para la entrevista ID {data.get('id_entrevista')}.")
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}. Mensaje recibido: {message}")
    except Exception as e:
        logger.error(f"Error inesperado durante el procesamiento de el feedback: {e}")



