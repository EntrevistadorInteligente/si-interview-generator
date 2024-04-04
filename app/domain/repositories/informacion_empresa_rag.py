from abc import ABC, abstractmethod

from app.infrastructure.schemas.hoja_de_vida_dto import InformacionEmpresaDto


class InformacionEmpresaRepository(ABC):

    @abstractmethod
    def obtener_por_id(self, id_informacion_empresa: str) -> InformacionEmpresaDto:
        raise NotImplemented

