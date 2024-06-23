from app.application.services.obtener_contextos_rags_service import ObtenerContextosRags
from app.application.services.generar_modelo_service import GenerarModeloContextoPdf
from app.application.services.pregunta_extractor import ExtractorRespuestasIa
from app.domain.entities.preparador_entrevista import PreparadorEntrevistaFactory
from app.domain.repositories.hoja_de_vida_rag import HojaDeVidaRepository
from app.domain.repositories.informacion_empresa_rag import InformacionEmpresaRepository
from app.domain.repositories.preparador_entrevista import PreparacionEntrevistaRepository
from app.domain.repositories.worker_manager import WorkerManagerRepository
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.infrastructure.schemas.hoja_de_vida_dto import SolicitudGeneracionEntrevistaDto, Worker


class GenerarEntrevistaService:

    def __init__(self, obtener_contextos_rags_service: ObtenerContextosRags,
                 generar_modelo_servicio: GenerarModeloContextoPdf,
                 hoja_de_vida_repository: HojaDeVidaRepository,
                 informacion_empresa_repository: InformacionEmpresaRepository,
                 preparacion_entrevista_repository: PreparacionEntrevistaRepository,
                 kafka_producer_service: KafkaProducerService,
                 worker_manager_repository: WorkerManagerRepository):
        self.obtener_contextos_rags_service = obtener_contextos_rags_service
        self.generar_modelo_servicio = generar_modelo_servicio
        self.hoja_de_vida_rag_repository = hoja_de_vida_repository
        self.informacion_empresa_repository = informacion_empresa_repository
        self.preparacion_entrevista_repository = preparacion_entrevista_repository
        self.kafka_producer_service = kafka_producer_service
        self.worker_manager_repository = worker_manager_repository

    async def ejecutar(self, preparacion_entrevista_dto: SolicitudGeneracionEntrevistaDto, worker: Worker) -> list[str]:

        text_chunks_hoja_de_vida = await (self.hoja_de_vida_rag_repository
                                          .obtener_por_id(preparacion_entrevista_dto.id_hoja_de_vida))

        informacion_empresa = await (self.informacion_empresa_repository.
                                     obtener_por_id(preparacion_entrevista_dto.id_informacion_empresa))

        text_chunks_con_contexto = await self.combinar_chunks(informacion_empresa, text_chunks_hoja_de_vida)

        response = await self.obtener_preguntas_entrevista(informacion_empresa, text_chunks_con_contexto, worker)

        await self.preparacion_entrevista_repository.add(PreparadorEntrevistaFactory
                                                         .create(preparacion_entrevista_dto.id_entrevista,
                                                                 text_chunks_con_contexto,
                                                                 response["input"],
                                                                 response["answer"]))
        await self.extraer_entrevista_desde_respuesta_modelo(preparacion_entrevista_dto, response)

    async def combinar_chunks(self, informacion_empresa, text_chunks_hoja_de_vida):

        text_chunks_hoja_de_vida_con_contexto = [f"EXPERIENCIA CANDIDATO: {chunk}" for chunk in
                                                 text_chunks_hoja_de_vida.hoja_de_vida_vect]
        text_chunks_informacion_empresa_con_contexto = [f"DETALLES EMPRESA: {chunk}" for chunk in
                                                        informacion_empresa.informacion_empresa_vect]

        text_chunks_con_contexto = text_chunks_hoja_de_vida_con_contexto + text_chunks_informacion_empresa_con_contexto
        return text_chunks_con_contexto

    async def obtener_preguntas_entrevista(self, informacion_empresa, text_chunks_con_contexto, worker: Worker):
        conversation_chain = await self.generar_modelo_entrevista(text_chunks_con_contexto, worker)
        prompt_entrevista = (
            f"Genera una entrevista técnica en ESPAÑOL para un candidato con perfil "
            f"'{informacion_empresa.perfil}' y nivel '{informacion_empresa.seniority}', ubicado en "
            f"'{informacion_empresa.pais}', para la vacante: '{informacion_empresa.descripcion_vacante}'. "
            """ Ejemplo de estructura de salida esperada:
            [
                {"question": "aqui podras tu pregunta"},
                {"question": "aqui podras tu pregunta"},
                ...
                {"question": "aqui podras tu pregunta"}
            ] """
            f"Incluye preguntas sobre el conocimiento técnico, experiencia y habilidades prácticas de programación. "
            f"Pero por supuesto orientado a lo que esta empresa preguntaria al candidato para cubrir este puesto. "
        )
        # Generar la respuesta de la IA basada en el prompt compuesto
        response = conversation_chain.invoke({
            'chat_history': [],
            "input": prompt_entrevista
        })

        return response

    async def generar_modelo_entrevista(self, text_chunks_con_contexto, worker):
        #worker = await self.worker_manager_repository.get_available_worker(1)
        ### Contextualize question ###
        contextualize_q_system_prompt = """
          Imagina que eres un experto entrevistador con acceso a la hoja de vida detallada de un candidato y 
          a información específica sobre una empresa y el puesto de trabajo para el cual se está considerando al candidato. 
          Tu tarea es crear preguntas de entrevista técnicas que estén altamente personalizadas para evaluar la idoneidad del 
          candidato para este puesto específico, teniendo en cuenta tanto sus habilidades y experiencias como las necesidades y 
          la cultura de la empresa. Formula preguntas que te permitan profundizar en su experiencia, conocimientos técnicos y 
          capacidad para adaptarse al entorno específico de la empresa. Recuerda no proporcionar respuestas a estas preguntas, 
          solo formula las preguntas más perspicaces y relevantes que se te ocurran.
          """
        qa_system_prompt = """Eres un experto en entrevistas laborales y tu tarea es responder en formato JSON. Genera 
        un conjunto de entre 5 a 7 preguntas (segun lo veas pertinente) en ESPAÑOL que podrían ser utilizadas en una entrevista real para evaluar a un candidato para 
        un puesto de trabajo. Las preguntas deben estar formuladas en español y abarcar diversos aspectos del perfil 
        profesional del candidato, como habilidades técnicas, experiencia, resolución de problemas y características personales.
        Cada pregunta debe estar contenida en un campo llamado 'question' dentro de un objeto JSON. Asegúrate de que 
        cada pregunta esté claramente formulada y de incluir todos los campos, incluso si el texto de entrada no 
        especifica todos los detalles claramente. El formato de salida esperado es un array de objetos JSON, donde 
        cada objeto tiene un único campo 'question'.
                {context}"""
        # Generar el contexto embebido para la conversación
        conversation_chain = self.generar_modelo_servicio.ejecutar(
            text_chunks=text_chunks_con_contexto, worker=worker,
            qa_system_prompt=qa_system_prompt,
            contextualize_q_system_prompt=contextualize_q_system_prompt,
            model_name="llama3-70b-8192"
        )
        return conversation_chain

    async def extraer_entrevista_desde_respuesta_modelo(self, preparacion_entrevista_dto, response):
        # Extrae el array del JSON
        array_data = ExtractorRespuestasIa.extract_array(response["answer"])
        # Encuentra las preguntas dentro del array extraído
        preguntas_formateadas = ExtractorRespuestasIa.find_keys(array_data, ['question'])
        await self.kafka_producer_service.send_message({
            "id_entrevista": preparacion_entrevista_dto.id_entrevista,
            "username": preparacion_entrevista_dto.username,
            "preguntas": preguntas_formateadas}, 'preguntasListenerTopic')




