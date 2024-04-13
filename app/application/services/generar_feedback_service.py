from typing import List

from app.application.services.obtener_contextos_rags_service import ObtenerContextosRags
from app.application.services.generar_modelo_contexto_pdf import GenerarModeloContextoPdf
from app.infrastructure.schemas.hoja_de_vida_dto import PreguntasDto


class GenerarFeedbackService:

    def __init__(self, obtener_contextos_rags_service: ObtenerContextosRags,
                 generar_modelo_contexto_pdf: GenerarModeloContextoPdf):
        self.obtener_contextos_rags_service = obtener_contextos_rags_service
        self.generar_modelo_contexto_pdf = generar_modelo_contexto_pdf

    async def ejecutar(self, feedback: PreguntasDto) -> PreguntasDto:

        for proceso in feedback.proceso_entrevista:
            proceso.feedback = "Hola"

        return feedback
