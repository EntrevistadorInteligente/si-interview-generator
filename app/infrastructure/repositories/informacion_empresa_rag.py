from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.domain.repositories.informacion_empresa_rag import InformacionEmpresaRepository

from app.infrastructure.schemas.hoja_de_vida_dto import InformacionEmpresaDto

# MongoDB connection URL
MONGO_URL = "mongodb://root:secret@localhost:27017/"
client = AsyncIOMotorClient(MONGO_URL)
database = client["recopilador_informacion_empresa_rag"]
collection = database["informacion_empresa"]


class InformacionEmpresaMongoRepository(InformacionEmpresaRepository):

    async def obtener_por_id(self, id_informacion_empresa: str) -> InformacionEmpresaDto:
        data = await collection.find_one({'_id': ObjectId(id_informacion_empresa)})
        if data:
            hoja_de_vida = InformacionEmpresaDto(descripcion_vacante=data.get('descripcion_vacante'),
                                                 empresa=data.get('empresa'),
                                                 perfil=data.get('perfil'),
                                                 seniority=data.get('seniority'),
                                                 pais=data.get('pais'),
                                                 informacion_empresa_vect=data.get('informacion_empresa_vect'))
            return hoja_de_vida
        else:
            raise Exception(f'InformacionEmpresa with id {id_informacion_empresa} not found')
