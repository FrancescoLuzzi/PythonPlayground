from typing import Any, Iterable, ClassVar
from threading import Lock
from json import dumps


class SchemableMeta(type):
    _schema_cache: ClassVar[dict[Any, dict[Any, Any]]] = {}
    _lock: ClassVar[Lock] = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._schema_cache:
                values_to_schematize = {
                    key: {"default": value, "type": type(value)}
                    for key, value in cls.__dict__.items()
                    if not key.startswith("_")
                }
                for key_name, key_type in cls.__annotations__.items():
                    values_to_schematize[key_name] = {"default": None, "type": key_type}
                cls._schema_cache[cls] = values_to_schematize
            instance = super().__call__(*args, **kwargs)
            setattr(instance, "schema", cls._schema_cache[cls])
            setattr(instance, "json_schema", dumps(cls._schema_cache[cls]))
            return instance

    @classmethod
    def get_json_schema_object_definition(cls):
        return cls._schema_cache


class BaseSchemable(metaclass=SchemableMeta):
    pass


class Simple(BaseSchemable):
    a: Iterable[int]
    b: list[float]
    c: str

    def __init__(self, a, b, c) -> None:
        self.a = a
        self.b = b
        self.c = c


ollare = Simple(1, 2, 3)
print(type(ollare.__class__))
print(SchemableMeta.get_json_schema_object_definition()[Simple]["a"]["type"])
