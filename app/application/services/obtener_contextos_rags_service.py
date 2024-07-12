import json
from http.client import HTTPException
from typing import Any

from langchain_text_splitters import CharacterTextSplitter

from app.domain.repositories.hoja_de_vida_rag import HojaDeVidaRepository
from app.domain.repositories.informacion_empresa_rag import InformacionEmpresaRepository


class ObtenerContextosRags:

    def __init__(self, hoja_de_vida_repository: HojaDeVidaRepository,
                 informacion_empresa_repository: InformacionEmpresaRepository):
        self.hoja_de_vida_rag_repository = hoja_de_vida_repository
        self.informacion_empresa_repository = informacion_empresa_repository

    async def ejecutar(self, id_hoja_de_vida: str, id_informacion_empresa: str) -> tuple[list[str], list[str]]:

        text_chunks_hoja_de_vida = await self.hoja_de_vida_rag_repository.obtener_por_id(id_hoja_de_vida)

        text_chunks_informacion_empresa = await (self.informacion_empresa_repository.
                                                 obtener_por_id(id_informacion_empresa))

        chunks_empresa = self.extraer_chuncks_json(text_chunks_informacion_empresa.informacion_empresa_vect)

        return text_chunks_hoja_de_vida.hoja_de_vida_vect, chunks_empresa

    def extraer_chuncks_json(self, object_to_chunk: Any) -> list[str]:
        json_string = json.dumps(object_to_chunk)

        # Comprobar si se extrajo algún texto
        if not json_string:
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del JSON")

        # Dividir el texto en chunks
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=800,
            chunk_overlap=50,
            length_function=len
        )

        text_chunks = text_splitter.split_text(json_string)

        return text_chunks
