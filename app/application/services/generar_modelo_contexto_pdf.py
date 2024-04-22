from typing import Any, List

from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import FAISS
import dotenv
from langchain_core.documents import Document

from app.domain.repositories.preparador_entrevista import PreparacionEntrevistaRepository


class GenerarModeloContextoPdf:

    def __init__(self, preparacion_entrevista_repository: PreparacionEntrevistaRepository):
        self.preparacion_entrevista_repository = preparacion_entrevista_repository

    def sin_memoria(self, text_chunks: list[str]) -> Any:
        dotenv.load_dotenv()
        # Crear vectorstore
        vectorstore = FAISS.from_texts(texts=text_chunks, embedding=OpenAIEmbeddings())

        # Crear conversation chain
        retriever = vectorstore.as_retriever()
        prompt = hub.pull("rlm/rag-prompt")
        llm = ChatOpenAI()

        retriever = vectorstore.as_retriever()

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
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        ### Answer question ###
        qa_system_prompt = """You are an assistant for question-answering tasks. \
        Use the following pieces of retrieved context to answer the question. \
        If you don't know the answer, just say that you don't know.

        {context}"""
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        return rag_chain




