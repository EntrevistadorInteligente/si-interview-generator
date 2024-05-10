from motor.motor_asyncio import AsyncIOMotorClient
from app.domain.entities.preparador_entrevista import PreparadorEntrevista
from app.domain.repositories.preparador_entrevista import PreparacionEntrevistaRepository
from app.infrastructure.schemas.preparador_entrevista_entity import PreparacionEntrevistaEntityRag


class PreparacionEntrevistaMongoRepository(PreparacionEntrevistaRepository):
    def __init__(self, mongo_url):
        self.mongo_url = mongo_url

    async def get_database(self):
        # Se crea una nueva instancia del cliente por cada solicitud.
        client = AsyncIOMotorClient(self.mongo_url)
        db = client["preparador_entrevista"]
        return db, client

    async def add(self, preparador_entrevista: PreparadorEntrevista) -> str:
        db, client = await self.get_database()
        collection = db["entrevista"]

        try:
            proceso_entrevista = PreparacionEntrevistaEntityRag(
                id_entrevista=preparador_entrevista.id_entrevista,
                contexto=preparador_entrevista.contexto,
                pregunta=preparador_entrevista.pregunta,
                respuesta=preparador_entrevista.respuesta,
            )
            result = await collection.insert_one(proceso_entrevista.dict())
            return str(result.inserted_id)
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    async def obtener_por_id(self, id_entrevista: str) -> PreparadorEntrevista:
        db, client = await self.get_database()
        collection = db["entrevista"]

        try:
            data = await collection.find_one({'id_entrevista': id_entrevista})
            if data:
                memoria_entrevista = PreparadorEntrevista(
                    id_entrevista=data.get('id_entrevista'),
                    contexto=data.get('contexto'),
                    pregunta=data.get('pregunta'),
                    respuesta=data.get('respuesta')
                )
                return memoria_entrevista
            else:
                raise Exception(f'Memoria Entrevista with id {id_entrevista} not found')
        except Exception as e:
            print(f"An error occurred: {e}")
            return None


