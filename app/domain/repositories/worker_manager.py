from abc import ABC, abstractmethod
from typing import Optional

from app.infrastructure.schemas.hoja_de_vida_dto import Worker


class WorkerManagerRepository(ABC):

    @abstractmethod
    async def get_available_worker(self, cantidad_tareas_a_ejecutar: int, estimado_tokens: int) -> Optional[Worker]:
        raise NotImplemented

    @abstractmethod
    async def release_worker(self, worker: Worker, requests_made: int, tokens_made: int):
        raise NotImplemented
