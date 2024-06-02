from abc import ABC, abstractmethod

from app.domain.entities.preparador_entrevista import PreparadorEntrevista


class PreparacionEntrevistaRepository(ABC):

    @abstractmethod
    async def add(self, preparador_entrevista: PreparadorEntrevista) -> str:
        raise NotImplemented

    @abstractmethod
    async def obtener_por_id(self, id_entrevista: str) -> PreparadorEntrevista:
        raise NotImplemented
