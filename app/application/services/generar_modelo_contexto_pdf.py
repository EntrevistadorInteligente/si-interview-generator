from typing import Any
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI


class GenerarModeloContextoPdf:
    def ejecutar(self, text_chunks: list[str]) -> Any:
        load_dotenv()
        # Crear vectorstore
        embeddings = OpenAIEmbeddings()
        # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")

        vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)

        # Crear conversation chain
        llm = ChatOpenAI()
        # llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature": 0.5, "max_length": 512})

        memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(),
            memory=memory
        )
        return conversation_chain
