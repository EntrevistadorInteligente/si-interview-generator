from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument

from app.domain.repositories.worker_manager import WorkerManagerRepository
from app.infrastructure.schemas.hoja_de_vida_dto import Worker


class WorkerManagerRepository(WorkerManagerRepository):
    def __init__(self, mongo_url):
        self.mongo_url = mongo_url

    async def get_database(self):
        client = AsyncIOMotorClient(self.mongo_url)
        db = client["preparador_entrevista"]
        return db, client

    async def get_available_worker(self, cantidad_tareas_a_ejecutar: int) -> Optional[Worker]:
        db, client = await self.get_database()
        collection = db["workers"]

        # Find one available worker with enough capacity and mark it as occupied
        worker_data = await collection.find_one_and_update(
            {
                "status": "available",
                "$expr": {
                    "$gte": [
                        {"$subtract": ["$request_limit", "$requests_made"]},
                        cantidad_tareas_a_ejecutar
                    ]
                }
            },
            {"$set": {"status": "occupied"}},
            return_document=ReturnDocument.AFTER
        )

        if worker_data:
            return Worker(**worker_data)
        return None

    async def release_worker(self, worker, requests_made: int):
        db, client = await self.get_database()
        collection = db["workers"]

        # Update worker status to available and increment requests made
        await collection.update_one(
            {"_id": worker.id},
            {
                "$inc": {"requests_made": requests_made},
                "$set": {"status": "available"}
            }
        )

