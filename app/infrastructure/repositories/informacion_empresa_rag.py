from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from app.domain.repositories.informacion_empresa_rag import InformacionEmpresaRepository
from app.infrastructure.schemas.hoja_de_vida_dto import InformacionEmpresaDto


class InformacionEmpresaMongoRepository(InformacionEmpresaRepository):
    def __init__(self, mongo_url):
        self.mongo_url = mongo_url

    async def get_database(self):
        client = AsyncIOMotorClient(self.mongo_url)
        return client["recopilador_informacion_empresa_rag"]

    async def obtener_por_id(self, id_informacion_empresa: str) -> InformacionEmpresaDto:

        db = await self.get_database()
        collection = db["informacion_empresa"]
        try:
            data = await collection.find_one({'_id': ObjectId(id_informacion_empresa)})
            if data:
                hoja_de_vida = InformacionEmpresaDto(descripcion_vacante=data.get('descripcionVacante'),
                                                     empresa=data.get('empresa'),
                                                     perfil=data.get('perfil'),
                                                     seniority=data.get('seniority'),
                                                     pais=data.get('pais'),
                                                     informacion_empresa_vect=data.get('informacionEmpresaVect'))
                return hoja_de_vida
            else:
                print(f'InformacionEmpresa with id {id_informacion_empresa} not found')
        except Exception as e:
            print(f"An error occurred: {e}")
            return None


