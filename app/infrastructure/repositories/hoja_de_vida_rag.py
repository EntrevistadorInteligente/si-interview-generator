from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.domain.repositories.hoja_de_vida_rag import HojaDeVidaRepository
from app.infrastructure.schemas.hoja_de_vida_dto import HojaDeVidaDto

# MongoDB connection URL
MONGO_URL = "mongodb://root:secret@localhost:27017/"
client = AsyncIOMotorClient(MONGO_URL)
database = client["analizador_hoja_vida_rag"]
collection = database["hoja_vida"]


class HojaDeVidaMongoRepository(HojaDeVidaRepository):

    async def obtener_por_id(self, id_hoja_de_vida: str) -> HojaDeVidaDto:
        data = await collection.find_one({'_id': ObjectId(id_hoja_de_vida)})
        if data:
            hoja_de_vida = HojaDeVidaDto(username=data.get('username'),
                                         hoja_de_vida_vect=data.get('hoja_de_vida_vect'))
            return hoja_de_vida
        else:
            raise Exception(f'HojaDeVida with id {id_hoja_de_vida} not found')
