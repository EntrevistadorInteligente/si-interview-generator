from pathlib import Path
from types import ModuleType
from typing import Iterator


class Handlers:
    ignored_files = {'__init__.py', '__pycache__'}
    handlers_base_path = Path(__file__).resolve().parent

    @classmethod
    def __all_module_names(cls) -> list:
        module_names = [
            f.stem for f in cls.handlers_base_path.glob('*.py')
            if f.name not in cls.ignored_files
        ]
        return module_names

    @classmethod
    def __module_namespace(cls, handler_name: str) -> str:
        return f"app.infrastructure.handlers.{handler_name}"

    @classmethod
    def modules(cls) -> list:
        return [cls.__module_namespace(name) for name in cls.__all_module_names()]

    @classmethod
    def iterator(cls) -> Iterator[ModuleType]:
        for module_name in cls.__all_module_names():
            module_namespace = cls.__module_namespace(module_name)
            import importlib
            handler = importlib.import_module(module_namespace)
            yield handler
