import logging

from fastapi import Depends, APIRouter
from dependency_injector.wiring import inject


# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix='/analizador',
    tags=['analizador']
)


@router.get('/', response_model=str)
@inject
def procesar_peticion_entrevista_message():
    print("procesar_peticion_entrevista_message")
    return "procesar_peticion_entrevista_message"




