from app.application.services.obtener_contextos_rags_service import ObtenerContextosRags
from app.application.services.generar_modelo_contexto_pdf import GenerarModeloContextoPdf
from app.domain.entities.preparador_entrevista import PreparadorEntrevista, PreparadorEntrevistaFactory
from app.domain.repositories.hoja_de_vida_rag import HojaDeVidaRepository
from app.domain.repositories.informacion_empresa_rag import InformacionEmpresaRepository
from app.domain.repositories.preparador_entrevista import PreparacionEntrevistaRepository
from app.infrastructure.schemas.hoja_de_vida_dto import HojaDeVidaDto, SolicitudGeneracionEntrevistaDto


class GenerarEntrevistaService:

    def __init__(self, obtener_contextos_rags_service: ObtenerContextosRags,
                 generar_modelo_contexto_pdf: GenerarModeloContextoPdf,
                 hoja_de_vida_repository: HojaDeVidaRepository,
                 informacion_empresa_repository: InformacionEmpresaRepository,
                 preparacion_entrevista_repository: PreparacionEntrevistaRepository,
                 kafka_producer_service) -> str:
        self.obtener_contextos_rags_service = obtener_contextos_rags_service
        self.generar_modelo_contexto_pdf = generar_modelo_contexto_pdf
        self.hoja_de_vida_rag_repository = hoja_de_vida_repository
        self.informacion_empresa_repository = informacion_empresa_repository
        self.preparacion_entrevista_repository = preparacion_entrevista_repository
        self.kafka_producer_service = kafka_producer_service

    async def ejecutar(self, preparacion_entrevista_dto: SolicitudGeneracionEntrevistaDto) -> list[str]:

        text_chunks_hoja_de_vida = await (self.hoja_de_vida_rag_repository
                                          .obtener_por_id(preparacion_entrevista_dto.id_hoja_de_vida))

        informacion_empresa = await (self.informacion_empresa_repository.
                                     obtener_por_id(preparacion_entrevista_dto.id_informacion_empresa))

        # Añadir descripciones contextuales a los textos
        text_chunks_hoja_de_vida_con_contexto = [f"EXPERIENCIA CANDIDATO: {chunk}" for chunk in
                                                 text_chunks_hoja_de_vida.hoja_de_vida_vect]
        text_chunks_informacion_empresa_con_contexto = [f"DETALLES EMPRESA: {chunk}" for chunk in
                                                        informacion_empresa.informacion_empresa_vect]

        # Combinar los chunks de texto con contexto
        text_chunks_con_contexto = text_chunks_hoja_de_vida_con_contexto + text_chunks_informacion_empresa_con_contexto

        # Generar el contexto embebido para la conversación
        conversation_chain = self.generar_modelo_contexto_pdf.ejecutar(
            text_chunks=text_chunks_con_contexto
        )

        # Crear el prompt para la simulación de la entrevista con la información clave de la empresa
        prompt_entrevista = (
            f"Genera una entrevista técnica en español para un candidato con perfil "
            f"'{informacion_empresa.perfil}' y nivel '{informacion_empresa.seniority}', ubicado en "
            f"'{informacion_empresa.pais}', para la vacante: '{informacion_empresa.descripcion_vacante}'. "
            f"Incluye preguntas sobre el conocimiento técnico, experiencia y habilidades prácticas de programación. "
            f"Pero por supuesto orientado a lo que esta emrpesa preguntaria al candidato para cubrir este puesto "
            f"Después de cada pregunta, coloca una línea de asteriscos así: ******. "
            f"Aquí tienes un ejemplo de cómo se debe ver cada pregunta:\n"
            f"¿Qué es DevOps? ******\n"
            f"¿Qué es DevOps? ******\n"
            f"¿Qué es DevOps? ******\n"
            f"¿Qué es DevOps? ******\n"
            f"¿Qué es DevOps? ******\n"
            f"Basado en eso, genera entre 10 a 20 "
            f"preguntas separadas por líneas de asteriscos como se muestra en el ejemplo. "
            f"ALERTA: el ejemplo es mero formato, no te bases en ello para la generacion de as preguntas , calidad de preguntas "
            f"u orientacion de preguntas"
        )

        # Generar la respuesta de la IA basada en el prompt compuesto

        response = conversation_chain.invoke({
            'chat_history': [],
            "input": prompt_entrevista
        })

        await self.preparacion_entrevista_repository.add(PreparadorEntrevistaFactory
                                                         .create(preparacion_entrevista_dto.id_entrevista,
                                                                 text_chunks_con_contexto,
                                                                 response["input"],
                                                                 response["answer"]))

        preguntas_formateadas = self.separar_preguntas(response['answer'])

        await self.kafka_producer_service.send_message({
            "id_entrevista": preparacion_entrevista_dto.id_entrevista,
            "preguntas": preguntas_formateadas}, 'preguntasListenerTopic')

    def separar_preguntas(self, texto, separador="******"):
        # Dividir el texto por el separador
        preguntas = texto.split(separador)
        # Remover espacios en blanco al principio y al final de cada pregunta
        preguntas = [pregunta.strip() for pregunta in preguntas if pregunta.strip()]
        return preguntas


