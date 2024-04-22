from abc import ABC, abstractmethod
from app.infrastructure.schemas.hoja_de_vida_dto import HojaDeVidaDto


class HojaDeVidaRepository(ABC):

    @abstractmethod
    async def obtener_por_id(self, id_hoja_de_vida: str) -> HojaDeVidaDto:
        raise NotImplemented

