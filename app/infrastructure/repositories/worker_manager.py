from datetime import datetime, timedelta
from typing import Optional

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

    async def get_available_worker(self, cantidad_tareas_a_ejecutar: int, estimado_tokens: int) -> Optional[Worker]:
        db, client = await self.get_database()
        collection = db["workers"]

        async with await client.start_session() as session:
            async with session.start_transaction():
                # Buscar worker disponible con capacidad suficiente por día y ordenar por último uso
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
                    sort=[("last_used", 1)],  # Ordenar por último uso ascendente
                    return_document=ReturnDocument.AFTER,
                    session=session
                )

                if worker_data:
                    last_used = worker_data.get("last_used")
                    now = datetime.utcnow()
                    if last_used and (now - last_used) < timedelta(minutes=1):
                        seconds_since_last_used = (now - last_used).total_seconds()
                        if seconds_since_last_used < 30:
                            max_requests_per_minute = 0.3 * 30  # 30% of 30 requests
                            max_tokens_per_minute = 0.3 * 30000  # 30% of 6000 tokens
                        else:
                            max_requests_per_minute = 0.7 * 30  # 70% of 30 requests
                            max_tokens_per_minute = 0.7 * 30000  # 70% of 6000 tokens

                        if (worker_data["requests_made_minute"] + cantidad_tareas_a_ejecutar > max_requests_per_minute or
                            worker_data["tokens_made_minute"] + estimado_tokens > max_tokens_per_minute):
                            # No cumple con los límites por minuto, liberar el worker y buscar otro
                            await collection.update_one(
                                {"_id": worker_data["_id"]},
                                {"$set": {"status": "available"}},
                                session=session
                            )
                            return None

                    # Si no fue utilizado en el último minuto o si cumple con los límites por minuto
                    updated_worker_data = await collection.find_one_and_update(
                        {"_id": worker_data["_id"]},
                        {
                            "$set": {
                                "last_used": now,
                                "requests_made_minute": worker_data.get("requests_made_minute", 0) + cantidad_tareas_a_ejecutar,
                                "tokens_made_minute": worker_data.get("tokens_made_minute", 0) + estimado_tokens
                            }
                        },
                        return_document=ReturnDocument.AFTER,
                        session=session
                    )

                    if updated_worker_data:
                        return Worker(**updated_worker_data)

        return None

    async def release_worker(self, worker: Worker, requests_made: int, tokens_made: int):
        db, client = await self.get_database()
        collection = db["workers"]

        now = datetime.utcnow()

        # Update worker status to available and update requests and tokens made
        await collection.update_one(
            {"_id": worker.id},
            {
                "$set": {
                    "status": "available",
                    "last_used": now,
                    "requests_made_minute": requests_made,
                    "tokens_made_minute": tokens_made
                },
                "$inc": {
                    "requests_made": requests_made
                }
            }
        )
