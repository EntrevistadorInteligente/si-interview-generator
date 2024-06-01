from app.domain.exceptions import PriceIsLessThanOrEqualToZero


class PreparadorEntrevista:

    def __init__(self, id_entrevista: str, contexto: list[str], pregunta: str, respuesta: str):
        self.__validate_price(id_entrevista)

        self.id_entrevista = id_entrevista
        self.contexto = contexto
        self.pregunta = pregunta
        self.respuesta = respuesta

    @staticmethod
    def __validate_price(id_entrevista: str):
        if not id_entrevista:
            raise PriceIsLessThanOrEqualToZero


class PreparadorEntrevistaFactory:

    @staticmethod
    def create(id_entrevista: str,  contexto: list[str], pregunta: str, respuesta: str) -> PreparadorEntrevista:
        return PreparadorEntrevista(id_entrevista, contexto, pregunta, respuesta)
