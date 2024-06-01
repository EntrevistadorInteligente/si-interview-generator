import json
from typing import Union, List, Any, Dict


class ExtractorRespuestasIa:

    @staticmethod
    def extract_array(data: Union[str, dict, list]) -> Union[dict, list]:
        """Extrae el array JSON del string dado."""
        if isinstance(data, str):
            try:
                start = data.index('[')
                end = data.rindex(']') + 1
                array_data = data[start:end]
                return json.loads(array_data)
            except (ValueError, json.JSONDecodeError) as e:
                print(f"Error extrayendo el array del JSON: {e}")
                return []
        elif isinstance(data, (dict, list)):
            return data
        else:
            print(f"Tipo de dato no soportado: {type(data)}")
            return []

    @staticmethod
    def find_keys(data: Union[dict, list], keys: List[str]) -> List[Dict[str, Any]]:
        """Encuentra recursivamente todas las claves de interés en el JSON y las agrupa en objetos completos."""
        results = []

        def extract(data: Union[dict, list], keys: List[str]) -> List[Dict[str, Any]]:
            """Función recursiva para extraer y agrupar las claves de interés."""
            if isinstance(data, dict):
                item = {}
                nested_results = []
                for key, value in data.items():
                    if key in keys:
                        item[key] = value
                    elif isinstance(value, (dict, list)):
                        nested_results.extend(extract(value, keys))
                if item:
                    nested_results.append(item)
                return nested_results
            elif isinstance(data, list):
                nested_results = []
                for element in data:
                    nested_results.extend(extract(element, keys))
                return nested_results
            return []

        results.extend(extract(data, keys))
        return results
