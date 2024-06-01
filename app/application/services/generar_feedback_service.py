import math
import time

from langchain_core.messages import HumanMessage, AIMessage

from app.application.services.generar_modelo_service import GenerarModeloContextoPdf
from app.application.services.obtener_contextos_rags_service import ObtenerContextosRags
from app.application.services.pregunta_extractor import ExtractorRespuestasIa
from app.domain.repositories.preparador_entrevista import PreparacionEntrevistaRepository
from app.domain.repositories.worker_manager import WorkerManagerRepository
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.infrastructure.schemas.hoja_de_vida_dto import PreguntasDto, FeedbackComentarioDto, FeedbackDto, Worker

CANTIDAD_PREGUNTAS_OPENIA = 5

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

        # Recuperar el contexto de la entrevista
        memoria_entrevista = await self.preparacion_entrevista_repository.obtener_por_id(preguntas.id_entrevista)

        conversation_chain = await self.generar_modelo_feedback(memoria_entrevista, worker)

        total_respuestas = len(preguntas.proceso_entrevista)

        if(worker is not None):
            es_instancia_groq = True
        else:
            es_instancia_groq = False

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
        ##worker = await self.worker_manager_repository.get_available_worker(total_respuestas)
        conversation_chain = (self.generar_modelo_servicio
                              .ejecutar(text_chunks=memoria_entrevista.contexto,
                                        worker=worker,
                                        qa_system_prompt=qa_system_prompt,
                                        contextualize_q_system_prompt=contextualize_q_system_prompt))
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
            feedback_response = conversation_chain.invoke({'chat_history': chat_history,
                                                           "input": feedback_prompt})
            feedback_comentarios = self.procesar_respuesta(respuestas_bloque, feedback_response['answer'])

            feedback_total.extend(feedback_comentarios)
        return FeedbackDto(
            id_entrevista=preguntas.id_entrevista,
            proceso_entrevista=feedback_total)

    def construir_prompt_feedback(self, respuestas, inicio_bloque):
        prompt = ("Genera feedback AMPLIO, constructivo y sincero para cada respuesta del candidato, debes evaluar su "
                  "contenido y ofrecer comentarios que resalten las fortalezas, "
                  "señalen las debilidades y propongan áreas para la mejora profesional. Este feedback debe ser útil para el candidato "
                  "y proporcionar una guía clara para su desarrollo profesional. para cada feedback un score del 1 al 10."
                  """ Ejemplo de estructura de salida esperada:
              [
                  {
                  "feedback": "aqui podras tu feedback AMPLIO (NO scores AQUI, solo FEEDBACK)",
                  "score": "(1 al 10)"
                  },
                  {
                  "feedback": "aqui podras tu feedback AMPLIO (NO scores AQUI, solo FEEDBACK)",
                  "score": "(1 al 10)"
                  },
                  ...
                  {
                  "feedback": "aqui podras tu feedback AMPLIO (NO scores AQUI, solo FEEDBACK)",
                  "score": "(1 al 10)"
                  },
              ] """
                  "A continuación, se te proporcionan las respuestas del candidato. "
                  "Genera el feedback en el formato JSON especificado para cada respuesta."
                  " Feddback en el feddbakc y score en el score IMPORTANTE. Respetar el formato\n\n"
                  )
        # Agregar respuestas
        for num, proceso in enumerate(respuestas, inicio_bloque + 1):  # Ajustar el número de pregunta correctamente
            prompt += f"Respuesta del candidato a la pregunta {num}: {proceso.respuesta}\n**Feedback:**\n"

        return prompt

    def procesar_respuesta(self, respuestas_bloque, feedback_response):

        array_data = ExtractorRespuestasIa.extract_array(feedback_response)
        # Encuentra las preguntas dentro del array extraído
        preguntas_formateadas = ExtractorRespuestasIa.find_keys(array_data, ['feedback', 'score'])

        # Crear una lista de FeedbackComentarioDto combinando los IDs y feedbacks
        min_length = min(len(respuestas_bloque), len(preguntas_formateadas))
        feedback_comentarios = [
            FeedbackComentarioDto(id_pregunta=respuestas_bloque[i].id_pregunta,
                                  feedback=preguntas_formateadas[i]['feedback'],
                                  score=preguntas_formateadas[i]['score'])
            for i in range(min_length)
        ]

        return feedback_comentarios


