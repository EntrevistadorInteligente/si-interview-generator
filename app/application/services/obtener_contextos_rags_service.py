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

        return text_chunks_hoja_de_vida.hoja_de_vida_vect, text_chunks_informacion_empresa.informacion_empresa_vect
