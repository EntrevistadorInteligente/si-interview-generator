import math
import time

from langchain_core.messages import HumanMessage, AIMessage

from app.application.services.obtener_contextos_rags_service import ObtenerContextosRags
from app.application.services.generar_modelo_contexto_pdf import GenerarModeloContextoPdf
from app.domain.repositories.preparador_entrevista import PreparacionEntrevistaRepository
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.infrastructure.schemas.hoja_de_vida_dto import PreguntasDto, FeedbackComentarioDto, FeedbackDto


class GenerarFeedbackService:

    def __init__(self, obtener_contextos_rags_service: ObtenerContextosRags,
                 generar_modelo_contexto_pdf: GenerarModeloContextoPdf,
                 preparacion_entrevista_repository: PreparacionEntrevistaRepository,
                 kafka_producer_service: KafkaProducerService):
        self.obtener_contextos_rags_service = obtener_contextos_rags_service
        self.generar_modelo_contexto_pdf = generar_modelo_contexto_pdf
        self.preparacion_entrevista_repository = preparacion_entrevista_repository
        self.kafka_producer_service = kafka_producer_service

    async def ejecutar(self, preguntas: PreguntasDto):
        inicio = time.time()  # Iniciar el contador de tiempo

        # Recuperar el contexto de la entrevista
        memoria_entrevista = await self.preparacion_entrevista_repository.obtener_por_id(preguntas.id_entrevista)
        conversation_chain = self.generar_modelo_contexto_pdf.ejecutar(text_chunks=memoria_entrevista.contexto)

        respuestas_por_bloque = 5
        total_respuestas = len(preguntas.proceso_entrevista)
        numero_bloques = math.ceil(total_respuestas / respuestas_por_bloque)

        feedback_total = []

        chat_history = [
            HumanMessage(content=memoria_entrevista.pregunta),
            AIMessage(content=memoria_entrevista.respuesta)
        ]

        for bloque in range(numero_bloques):
            inicio_bloque = bloque * respuestas_por_bloque
            fin_bloque = inicio_bloque + respuestas_por_bloque
            respuestas_bloque = preguntas.proceso_entrevista[inicio_bloque:fin_bloque]

            feedback_prompt = self.construir_prompt_feedback(respuestas_bloque, inicio_bloque)
            feedback_response = conversation_chain.invoke({'chat_history': chat_history,
                                                           "input": feedback_prompt})
            feedback_comentarios = self.procesar_respuesta(respuestas_bloque, feedback_response['answer'])

            feedback_total.extend(feedback_comentarios)

        # Crear objeto FeedbackDto para enviar al backend de Java
        # Crear objeto FeedbackDto para enviar al backend de Java
        feedback_dto = FeedbackDto(
            id_entrevista=preguntas.id_entrevista,
            proceso_entrevista=feedback_total
        )

        await self.kafka_producer_service.send_message(feedback_dto.dict(), 'feedbackListenerTopic')

    def construir_prompt_feedback(self, respuestas, inicio_bloque):
        prompt = ("A continuación, se te presentan respuestas de un candidato a una serie de preguntas técnicas. "
                  "Tu tarea es proporcionar feedback específico y constructivo para cada respuesta. Para cada respuesta del candidato, "
                  "debes evaluar su contenido y ofrecer comentarios que resalten las fortalezas, señalen las debilidades y propongan áreas "
                  "para la mejora profesional. Este feedback debe ser útil para el candidato y proporcionar una guía clara para su desarrollo "
                  "Ejemplo de cómo dar feedback:\n"
                  "aqui darias tu feedback muy completo como entrevistador que eres\n"
                  "**Feedback:**n"
                  "aqui darias tu feedback muy completo como entrevistador que eres\n"
                  "**Feedback:**n"
                  "aqui darias tu feedback muy completo como entrevistador que eres\n"
                  "**Feedback:**n"
                  "Por favor, estructura tu feedback como se indica en el ejemplo Manteniendo siempre la separacion "
                  "entre respuestas por **Feedback:**\n"
                  "esta estructura de SEPARACION es INDISPENSABLE, no la omitas.Ni la cambies por nada\n\n"
                  "profesional. Las preguntas y respuestas están separadas por líneas de asteriscos, como se muestra a continuación.\n\n")
        # Agregar respuestas
        for num, proceso in enumerate(respuestas, inicio_bloque + 1):  # Ajustar el número de pregunta correctamente
            prompt += f"Respuesta del candidato a la pregunta {num}: {proceso.respuesta}\n**Feedback:**\n"

        return prompt

    def procesar_respuesta(self, respuestas_bloque, feedback_response):
        # Dividir la respuesta del modelo en partes según tu lógica
        feedbacks = feedback_response.split("**Feedback:**")

        # Elimina el primer elemento en caso de que el modelo genere una separación no deseada
        if feedbacks[0] == '':
            feedbacks.pop(0)

        # Crear una lista de FeedbackComentarioDto combinando los IDs y feedbacks
        min_length = min(len(respuestas_bloque), len(feedbacks))
        feedback_comentarios = [
            FeedbackComentarioDto(id_pregunta=respuestas_bloque[i].id_pregunta, feedback=feedbacks[i])
            for i in range(min_length)
        ]

        return feedback_comentarios


