from typing import List, Optional, Any

from pydantic import BaseModel, Field, validator
from bson import ObjectId
from enum import Enum


class HojaDeVidaDto(BaseModel):
    username: Optional[str] = None
    hoja_de_vida_vect: Optional[list[str]] = None


class InformacionEmpresaDto(BaseModel):
    descripcion_vacante: Optional[str] = None
    empresa: Optional[str] = None
    perfil: Optional[str] = None
    seniority: Optional[str] = None
    pais: Optional[str] = None
    informacion_empresa_vect: Optional[list[Any]] = None


class InformacionEmpresaSolicitudDto(BaseModel):
    empresa: Optional[str] = None
    perfil: Optional[str] = None
    seniority: Optional[str] = None
    pais: Optional[str] = None
    descripcion_vacante: Optional[str] = None
    id_informacion_empresa_rag: Optional[str] = None


class SolicitudGeneracionEntrevistaDto(BaseModel):
    id_entrevista: Optional[str] = None
    id_hoja_de_vida: Optional[str] = None
    username: Optional[str] = None
    id_informacion_empresa: Optional[str] = None


class EstadoProcesoEnum(str, Enum):
    AC = "AC"
    CVA = "CVA"
    FN = "FN"


class ProcesoEntrevistaDto(BaseModel):
    uuid: Optional[str] = None
    estado: EstadoProcesoEnum
    fuente: Optional[str] = None
    error: Optional[str] = None


class MensajeAnalizadorDto(BaseModel):
    proceso_entrevista: ProcesoEntrevistaDto
    id_entrevista: Optional[str] = None,
    hoja_de_vida: HojaDeVidaDto


class EntrevistaDto(BaseModel):
    id_entrevista: Optional[str] = None
    preguntas: List[str] = []


class RespuestaComentarioDto(BaseModel):
    id_pregunta: Optional[str] = None
    respuesta: Optional[str] = None


class PreguntasDto(BaseModel):
    id_entrevista: Optional[str] = None
    proceso_entrevista: List[RespuestaComentarioDto] = []


class FeedbackComentarioDto(BaseModel):
    id_pregunta: Optional[str] = None
    feedback: Optional[str] = None
    score: Optional[str] = None


class FeedbackDto(BaseModel):
    id_entrevista: Optional[str] = None
    proceso_entrevista: List[FeedbackComentarioDto] = []


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class Worker(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    request_limit: int
    requests_made: int
    status: str
    api_id: str









