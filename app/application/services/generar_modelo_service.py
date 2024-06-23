from typing import Any, List

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import FAISS
import dotenv

from app.domain.repositories.preparador_entrevista import PreparacionEntrevistaRepository
from app.infrastructure.schemas.hoja_de_vida_dto import Worker


class GenerarModeloContextoPdf:

    def __init__(self, preparacion_entrevista_repository: PreparacionEntrevistaRepository):
        self.preparacion_entrevista_repository = preparacion_entrevista_repository

    def ejecutar(self, text_chunks: list[str], worker: Worker,
                 qa_system_prompt,
                 contextualize_q_system_prompt,
                 model_name) -> Any:
        dotenv.load_dotenv()
        # Crear vectorstore
        vectorstore = FAISS.from_texts(texts=text_chunks, embedding=OpenAIEmbeddings())

        if worker is not None:
            # Use ChatGroq if worker is available
            llm = ChatGroq(temperature=0, groq_api_key=worker.api_id, model_name=model_name)
        else:
            # Use OpenAI if no worker is available
            llm = ChatOpenAI(temperature=0)

        retriever = vectorstore.as_retriever()

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




