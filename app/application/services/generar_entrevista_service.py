from app.application.services.obtener_contextos_rags_service import ObtenerContextosRags
from app.application.services.generar_modelo_contexto_pdf import GenerarModeloContextoPdf
from app.infrastructure.schemas.hoja_de_vida_dto import HojaDeVidaDto, SolicitudGeneracionEntrevistaDto
from fastapi import HTTPException


class GenerarEntrevistaService:

    def __init__(self, obtener_contextos_rags_service: ObtenerContextosRags,
                 generar_modelo_contexto_pdf: GenerarModeloContextoPdf) -> str:
        self.obtener_contextos_rags_service = obtener_contextos_rags_service
        self.generar_modelo_contexto_pdf = generar_modelo_contexto_pdf

    async def ejecutar(self, preparacion_entrevista_dto: SolicitudGeneracionEntrevistaDto) -> str:

        preguntas = ["¿Qué diferencias se encuentran entre interfaces y clases?",
                     "¿Qué problemas se pueden encontrar dentro de la multi herencia?",
                     "¿Por qué se necesitan métodos por defecto y pueden éstos anular un método Object?",
                     "¿Cómo se pueden encontrar duplicados en una base de datos relacional utilizando SQL?"]

        (text_chunks_hoja_de_vida,
         text_chunks_informacion_empresa) = await (self.obtener_contextos_rags_service
                                                   .ejecutar(preparacion_entrevista_dto.id_hoja_de_vida,
                                                             preparacion_entrevista_dto.id_informacion_empresa))

        return preguntas
