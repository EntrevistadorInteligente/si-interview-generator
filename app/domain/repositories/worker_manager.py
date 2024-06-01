from abc import ABC, abstractmethod
from typing import Optional

from app.infrastructure.schemas.hoja_de_vida_dto import Worker


class WorkerManagerRepository(ABC):

    @abstractmethod
    async def get_available_worker(self, cantidad_tareas_a_ejecutar: int) -> Optional[Worker]:
        raise NotImplemented

    @abstractmethod
    async def release_worker(self, worker, requests_made: int):
        raise NotImplemented
