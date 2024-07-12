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
        generar_entrevista_service: GenerarEntrevistaService = Depends(Provide[Container.generar_entrevista_service]),
        worker_manager_repository=Depends(Provide[Container.worker_manager_repository])):
    worker = None
    try:
        data = json.loads(message.decode('utf-8'))
        worker = await worker_manager_repository.get_available_worker(1, 5000)
        preparacion_entrevista_dto = SolicitudGeneracionEntrevistaDto(
            id_entrevista=data.get('id_entrevista'),
            id_hoja_de_vida=data.get('id_hoja_de_vida'),
            username=data.get('username'),
            id_informacion_empresa=data.get('id_informacion_empresa')
        )
        # Procesar y loguear a la cola
        await generar_entrevista_service.ejecutar(preparacion_entrevista_dto, worker)
        logger.info(f"Procesamiento completado para la entrevista ID {data.get('id_entrevista')}.")

    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}. Mensaje recibido: {message}")
    except Exception as e:
        logger.error(f"Error inesperado durante el procesamiento de la entrevista: {e}")
    finally:
        if worker:
            await worker_manager_repository.release_worker(worker, 1, 5001)


@router.get('/2', response_model=str)
@inject
async def procesar_peticion_feedback_message(
        message, generar_feedback_service: GenerarFeedbackService =
        Depends(Provide[Container.generar_feedback_service]),
        worker_manager_repository=Depends(Provide[Container.worker_manager_repository])):
    worker = None
    total_respuestas = 0
    try:
        data = json.loads(message.decode('utf-8'))
        preguntas = PreguntasDto(**data)
        total_respuestas = len(preguntas.proceso_entrevista)
        worker = await worker_manager_repository.get_available_worker(total_respuestas, 10000)
        await generar_feedback_service.ejecutar(PreguntasDto(**data), worker)
        logger.info(f"Procesamiento de feedback completado para la entrevista ID {data.get('id_entrevista')}.")
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}. Mensaje recibido: {message}")
    except Exception as e:
        logger.error(f"Error inesperado durante el procesamiento de el feedback: {e}")
    finally:
        if worker:
            await worker_manager_repository.release_worker(worker, total_respuestas, 10001)




