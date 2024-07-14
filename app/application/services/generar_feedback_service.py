import math
import time
import re
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError

from langchain_core.messages import HumanMessage, AIMessage

from app.application.services.generar_modelo_service import GenerarModeloContextoPdf
from app.application.services.obtener_contextos_rags_service import ObtenerContextosRags
from app.application.services.pregunta_extractor import ExtractorRespuestasIa
from app.domain.repositories.preparador_entrevista import PreparacionEntrevistaRepository
from app.domain.repositories.worker_manager import WorkerManagerRepository
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.infrastructure.schemas.hoja_de_vida_dto import PreguntasDto, FeedbackComentarioDto, FeedbackDto, Worker

CANTIDAD_PREGUNTAS_OPENIA = 4
CANTIDAD_PREGUNTAS_GROQ = 2

class GenerarFeedbackService:

    def __init__(self, obtener_contextos_rags_service: ObtenerContextosRags,
                 generar_modelo_servicio: GenerarModeloContextoPdf,
                 preparacion_entrevista_repository: PreparacionEntrevistaRepository,
                 kafka_producer_service: KafkaProducerService,
                 worker_manager_repository: WorkerManagerRepository):
        self.obtener_contextos_rags_service = obtener_contextos_rags_service
        self.generar_modelo_servicio = generar_modelo_servicio
        self.preparacion_entrevista_repository = preparacion_entrevista_repository
        self.kafka_producer_service = kafka_producer_service
        self.worker_manager_repository = worker_manager_repository

    async def ejecutar(self, preguntas: PreguntasDto, worker: Worker):
        inicio = time.time()

        memoria_entrevista = await self.preparacion_entrevista_repository.obtener_por_id(preguntas.id_entrevista)

        conversation_chain = await self.generar_modelo_feedback(memoria_entrevista, worker)

        total_respuestas = len(preguntas.proceso_entrevista)

        es_instancia_groq = worker is not None

        feedback_dto = await self.generar_feedback_entrevista(conversation_chain, memoria_entrevista, preguntas,
                                                              total_respuestas, es_instancia_groq)

        await self.kafka_producer_service.send_message(feedback_dto.dict(), 'feedbackListenerTopic')

    async def generar_modelo_feedback(self, memoria_entrevista, worker):
        contextualize_q_system_prompt = """
        Imagina que eres un experto entrevistador con acceso a la hoja de vida detallada de un candidato y 
        a información específica sobre una empresa y el puesto de trabajo para el cual se está considerando al candidato. 
        Tu tarea es proporcionar retroalimentación constructiva y detallada que pueda ayudar al candidato a mejorar sus habilidades 
        y prepararse mejor para futuras entrevistas. La retroalimentación debe ser altamente personalizada, teniendo en cuenta tanto 
        sus habilidades y experiencias como las necesidades y la cultura de la empresa. Formula tus comentarios de manera que el candidato 
        pueda comprender claramente sus fortalezas y áreas de mejora, y ofrécele consejos prácticos sobre cómo puede crecer y mejorar.
        """
        qa_system_prompt = """
        Eres un experto en entrevistas laborales y tu tarea es proporcionar retroalimentación constructiva y detallada en formato JSON.
        Genera un conjunto de comentarios personalizados que podrían ser utilizados para ayudar a un candidato a mejorar en su carrera profesional.
        La retroalimentación debe estar formulada en español y abarcar diversos aspectos del perfil profesional del candidato, como habilidades técnicas,
        experiencia, resolución de problemas y características personales. Asegúrate de que cada comentario esté claramente formulado y de incluir 
        todos los campos, incluso si el texto de entrada no especifica todos los detalles claramente. El formato de salida esperado es un array de 
        objetos JSON, donde cada objeto tiene un único campo 'feedback' y otro como 'score'.
                {context}"""

        conversation_chain = (self.generar_modelo_servicio
                              .ejecutar(text_chunks=memoria_entrevista.contexto,
                                        worker=worker,
                                        qa_system_prompt=qa_system_prompt,
                                        contextualize_q_system_prompt=contextualize_q_system_prompt,
                                        model_name="llama3-8b-8192"))
        return conversation_chain

    async def generar_feedback_entrevista(self, conversation_chain, memoria_entrevista, preguntas,
                                          total_respuestas,
                                          es_instancia_groq):
        chat_history = [
            HumanMessage(content=memoria_entrevista.pregunta),
            AIMessage(content=memoria_entrevista.respuesta)
        ]

        respuestas_por_bloque = CANTIDAD_PREGUNTAS_GROQ if es_instancia_groq else CANTIDAD_PREGUNTAS_OPENIA
        numero_bloques = math.ceil(total_respuestas / respuestas_por_bloque)
        feedback_total = []
        for bloque in range(numero_bloques):
            inicio_bloque = bloque * respuestas_por_bloque
            fin_bloque = inicio_bloque + respuestas_por_bloque
            respuestas_bloque = preguntas.proceso_entrevista[inicio_bloque:fin_bloque]

            feedback_prompt = self.construir_prompt_feedback(respuestas_bloque, inicio_bloque)
            feedback_response = self.invoke_with_retry(conversation_chain, chat_history, feedback_prompt)
            feedback_comentarios = self.procesar_respuesta(respuestas_bloque, feedback_response['answer'])

            feedback_total.extend(feedback_comentarios)
        return FeedbackDto(
            id_entrevista=preguntas.id_entrevista,
            proceso_entrevista=feedback_total)

    def construir_prompt_feedback(self, respuestas, inicio_bloque):
        prompt = (
            "Eres un evaluador experto en entrevistas de trabajo. Tu tarea es proporcionar feedback CRÍTICO y HONESTO "
            "en ESPAÑOL para cada respuesta del candidato. NO seas complaciente. Evalúa la calidad y relevancia de cada respuesta. "
            "Si la respuesta no tiene sentido o no es relevante, debes señalarlo claramente y asignar una puntuación baja. "
            "Ofrece comentarios que resalten las fortalezas reales, señalen las debilidades concretas y propongan áreas específicas para la mejora profesional. "
            "Asigna un score del 1 al 10 basado ESTRICTAMENTE en la calidad y relevancia de la respuesta:\n"
            "1-3: Respuesta sin sentido o completamente irrelevante\n"
            "4-5: Respuesta pobre o mayormente irrelevante\n"
            "6-7: Respuesta aceptable pero con áreas significativas de mejora\n"
            "8-9: Buena respuesta con pequeñas áreas de mejora\n"
            "10: Respuesta excelente y completa\n\n"
            "FORMATO de estructura de salida QUE DEBES ENTREGAR. JSON con LOS CAMPOS OBLIGATORIOS:\n"
            "[\n"
            "    {\n"
            "    \"feedback\": \"Aquí tu feedback DETALLADO y CRÍTICO (NO scores AQUI, solo FEEDBACK)\",\n"
            "    \"score\": \"(1 al 10 justificado)\"\n"
            "    }\n"
            "]\n"
            "IMPORTANTE: Si la respuesta no tiene sentido o es claramente irrelevante, asigna un score bajo (1-3) "
            "y explica en el feedback por qué la respuesta no es adecuada.\n\n"
            "A continuación, se te proporcionan las respuestas del candidato. Evalúa cada una críticamente:\n\n"
        )
        for num, proceso in enumerate(respuestas, inicio_bloque + 1):

            prompt += f"Respuesta del candidato a la pregunta # {num}: {proceso.respuesta}\n**Evaluación:**\n\n"

        return prompt

    def procesar_respuesta(self, respuestas_bloque, feedback_response):
        array_data = ExtractorRespuestasIa.extract_array(feedback_response)
        preguntas_formateadas = ExtractorRespuestasIa.find_keys(array_data, ['feedback', 'score'])

        min_length = min(len(respuestas_bloque), len(preguntas_formateadas))
        feedback_comentarios = [
            FeedbackComentarioDto(id_pregunta=respuestas_bloque[i].id_pregunta,
                                  feedback=preguntas_formateadas[i]['feedback'],
                                  score=preguntas_formateadas[i]['score'])
            for i in range(min_length)
        ]

        return feedback_comentarios

    @retry(stop=stop_after_attempt(5),
           wait=wait_exponential(multiplier=1, min=4, max=60),
           retry=retry_if_exception_type(RateLimitError))
    def invoke_with_retry(self, conversation_chain, chat_history, feedback_prompt):
        try:
            return conversation_chain.invoke({'chat_history': chat_history, "input": feedback_prompt})
        except RateLimitError as e:
            retry_after = self.extract_retry_after(str(e))
            retry_after += 30
            print(f"Rate limit reached. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            raise e  # Re-raise the exception to trigger the retry

    def extract_retry_after(self, error_message):
        match = re.search(r'Please try again in (\d+\.\d+)s', error_message)
        if match:
            return float(match.group(1))
        return 1
