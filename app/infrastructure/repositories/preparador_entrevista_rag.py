from motor.motor_asyncio import AsyncIOMotorClient
from app.domain.entities.preparador_entrevista import PreparadorEntrevista
from app.domain.repositories.preparador_entrevista import PreparacionEntrevistaRepository
from app.infrastructure.schemas.preparador_entrevista_entity import PreparacionEntrevistaEntityRag

# MongoDB connection URL
MONGO_URL = ("mongodb+srv://entrevistador:swJTdyxG8pJczD0m@clusterentrevistadoria.rtuhiw6.mongodb.net/?retryWrites=true"
             "&w=majority&appName=ClusterEntrevistadorIA")
client = AsyncIOMotorClient(MONGO_URL)
database = client["preparador_entrevista"]
collection = database["entrevista"]


class PreparacionEntrevistaMongoRepository(PreparacionEntrevistaRepository):

    async def add(self, preparador_entrevista: PreparadorEntrevista) -> str:
        proceso_entrevista = PreparacionEntrevistaEntityRag(
            id_entrevista=preparador_entrevista.id_entrevista,
            contexto=preparador_entrevista.contexto,
            pregunta=preparador_entrevista.pregunta,
            respuesta=preparador_entrevista.respuesta,
        )

        result = await collection.insert_one(proceso_entrevista.dict())
        return str(result.inserted_id)

    async def obtener_por_id(self, id_entrevista: str) -> PreparadorEntrevista:
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

