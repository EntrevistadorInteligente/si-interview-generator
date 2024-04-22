from typing import List

from langchain_core.messages import HumanMessage, AIMessage

from app.application.services.obtener_contextos_rags_service import ObtenerContextosRags
from app.application.services.generar_modelo_contexto_pdf import GenerarModeloContextoPdf
from app.domain.repositories.preparador_entrevista import PreparacionEntrevistaRepository
from app.infrastructure.schemas.hoja_de_vida_dto import PreguntasDto


class GenerarFeedbackService:

    def __init__(self, obtener_contextos_rags_service: ObtenerContextosRags,
                 generar_modelo_contexto_pdf: GenerarModeloContextoPdf,
                 preparacion_entrevista_repository: PreparacionEntrevistaRepository):
        self.obtener_contextos_rags_service = obtener_contextos_rags_service
        self.generar_modelo_contexto_pdf = generar_modelo_contexto_pdf
        self.preparacion_entrevista_repository = preparacion_entrevista_repository

    async def ejecutar(self, feedback: PreguntasDto) -> PreguntasDto:
        # Recuperar el contexto de entrevista
        memoria_entrevista = await self.preparacion_entrevista_repository.obtener_por_id(feedback.id_entrevista)

        # Reconstruir la conversación con memoria
        conversation_chain = self.generar_modelo_contexto_pdf.sin_memoria(text_chunks=memoria_entrevista.contexto)

        # Formatear las preguntas y respuestas para el feedback
        feedback_prompt = (
            "Evalúa las respuestas del candidato considerando su relevancia, profundidad y alineación con la pregunta correspondiente."
            "Ofrece comentarios constructivos que incluyan puntos fuertes, áreas de mejora y sugerencias específicas."
            "Recuerda eres el entrevistador y debes hablar y coportarte como tal"
            "A continuación se presentan una serie de respuestas de el candidato. A las preguntas que le habias dado"
            "las respuestas estan enumeradas en el mismo orden en el que se las diste. Si todas las respuestas no tienen sentido"
            "y me refiero a escenarios de borde donde no tiene nada que ver con el tema a tratar"
            "no que el usuario se haya equivocado en la respuesta, Simplemente di 'ALERTA SINSENTIDO' como respuesta GENERAL "
            "en caso en que toda la entrevista global no por pregunta no tenga sentido, si existen preguntas sin sentido da un feedback indicando"
            "que es buena idea responder en las entrevistas cosas con sentido"
            "de lo contrario genera el feedback completo con los detalles rpeviamente dados"
            "Si no puedes proporcionar todo el feedback de una respuesta en este mensaje, "
            "termina con la frase 'Continúa en la siguiente respuesta...' y yo solicitaré el resto."
            "Por favor, genera un feedback constructivo y específico para cada respuesta del candidato:\n\n")

        # Agregar cada pregunta y respuesta al prompt con instrucciones
        for num, proceso in enumerate(feedback.proceso_entrevista, 1):
            feedback_prompt += f"Respuesta del candidato a la pregunta {num}: {proceso.respuesta} ******\n"

        # Añadir instrucciones para dividir el feedback si es muy largo
        feedback_prompt += ("\nSi no has terminado con el feedback completo, escribe 'Continúa en la siguiente respuesta...' "
                            "para que éudas terminar con lo faltante trata de resolver la mayor cantidad prebguntas "
                            "posibles en tu ventana de contexto\n")

        feedback_prompt1 = (
            "A continuación, se te presentan respuestas de un candidato a una serie de preguntas técnicas. "
            "Tu tarea es proporcionar feedback específico y constructivo para cada respuesta. Para cada respuesta del candidato, "
            "debes evaluar su contenido y ofrecer comentarios que resalten las fortalezas, señalen las debilidades y propongan áreas "
            "para la mejora profesional. Este feedback debe ser útil para el candidato y proporcionar una guía clara para su desarrollo "
            "profesional. Las preguntas y respuestas están separadas por líneas de asteriscos, como se muestra a continuación. "
            "Tu feedback debe seguir inmediatamente después de cada respuesta del candidato. Por favor, estructura tu feedback como se "
            "indica en el ejemplo.\n\n"
        )

        # Ejemplo para guiar a la IA
        feedback_prompt1 += (
            "Ejemplo de cómo dar feedback:\n"
            "Feedback pregunta 1: Valoramos tu enfoque en la priorización y el enfoque en los resultados. Sugerimos también mencionar "
            "técnicas específicas de manejo del estrés para una respuesta más completa. "
            "******\n"
            "----------------------------------------\n\n"
        )

        # Generar la sección para cada respuesta del candidato
        for num, proceso in enumerate(feedback.proceso_entrevista, 1):
            feedback_prompt1 += (
                f"Pregunta  {num}: {proceso.pregunta}\n"
                f"Respuesta pregunta {num}: {proceso.respuesta}\n"
                f"******\n"
                "----------------------------------------\n\n"
            )

        # Indicaciones finales para la IA
        feedback_prompt1 += (
            "Por favor, asegúrate de que tu feedback sea informativo, específico y orientado a la mejora continua del candidato. "
            "Si alguna respuesta del candidato no tiene sentido o no está relacionada con la pregunta, usa 'ALERTA SINSENTIDO' "
            "y proporciona consejos sobre cómo el candidato puede mejorar la relevancia de sus respuestas en el futuro. "
            "Si tu feedback para una respuesta es demasiado largo, termina con 'Continúa en la siguiente respuesta...' y "
            "'IMPORTANTE RECUERDA SIEMPRE EL MENSAJE FINAL 'seguiré recopilando el feedback en un mensaje adicional.\n"
        )

        chat_history = [
            HumanMessage(content=memoria_entrevista.pregunta),
            AIMessage(content=memoria_entrevista.respuesta)
        ]

        # Generar el feedback de la IA en un solo llamado
        feedback_response = conversation_chain.invoke({
            'chat_history': chat_history,
            "input": feedback_prompt1
        })
        # Procesar la respuesta de la IA y asignar el feedback
        # Aquí necesitarás una función que extraiga el feedback de la respuesta de la IA y lo asocie con cada pregunta.
        respuesta = feedback_response['answer']

        if respuesta.lower() == "ALERTA SINSENTIDO".lower():
            feedback_valido = True
        else:
            feedback_valido = False

        feedback.proceso_entrevista = await self.process_feedback(feedback_response['answer'],
                                                                  conversation_chain)

        return feedback

    async def process_feedback(self, feedback_text, conversation_chain):
        # Dividir el feedback en partes, según la frase clave
        feedback_parts = feedback_text.split('Continúa en la siguiente respuesta')
        feedback_final = []
        for part in feedback_parts:
            # Procesar cada parte para ver si necesita más información
            if part.strip().endswith('...'):
                feedback_response = conversation_chain.invoke({
                    "input": "Continúa"
                })
                continue
            feedback_final.append(part.strip())

        return feedback_final


