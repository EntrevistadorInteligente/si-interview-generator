from typing import Optional

from pydantic import BaseModel


class PreparacionEntrevistaEntityRag(BaseModel):
    id_entrevista: Optional[str] = None
    contexto: list[str] = None
    pregunta: Optional[str] = None
    respuesta: Optional[str] = None



