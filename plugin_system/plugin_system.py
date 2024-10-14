from typing import Dict, Any, List, NamedTuple, Tuple, Callable, Self
import inspect
import importlib.util as il_utils
from types import ModuleType


class PluginException(Exception):
    pass


class PluginMissingFunctionException(PluginException):
    pass


class PluginMissmatchFunctionException(PluginException):
    pass


class PluginFunction(NamedTuple):
    name: str
    argument_types: Tuple[type]
    return_type: type

    def __str__(self):
        return f"{self.name}{self.argument_types}->{self.return_type or 'None'}"

    def eq_argument_types(self, other: Self) -> bool:
        for s, o in zip(self.argument_types, other.argument_types):
            if s == inspect._empty or o == inspect._empty:
                continue
            if s != o:
                return False
        return True

    def eq_return_type(self, other: Self) -> bool:
        s = self.return_type
        o = other.return_type
        if s == inspect._empty or o == inspect._empty:
            return True
        return s == o


def plugin_from_function(
    func: Callable[[Any], Any], drop_first_argument: bool
) -> PluginFunction:
    sign = inspect.signature(func)
    attrs = tuple(p.annotation for p in sign.parameters.values())
    attrs = attrs[int(drop_first_argument) :]
    ret = sign.return_annotation
    return PluginFunction(func.__name__, attrs, ret)


def _validate_plugin(wanted_functions: List[PluginFunction], module: ModuleType):
    for wanted_func in wanted_functions:
        func = getattr(module, wanted_func.name)
        if not inspect.isfunction(func):
            raise PluginMissingFunctionException(
                f"found {wanted_func.name} but is not a function. Wanted {wanted_func}"
            )
        plugin_func = plugin_from_function(func, False)
        if not wanted_func.eq_argument_types(plugin_func):
            raise PluginMissmatchFunctionException(
                f"found arguments {plugin_func} but wanted {wanted_func}"
            )
        if not wanted_func.eq_return_type(plugin_func):
            raise PluginMissmatchFunctionException(
                f"found return type {plugin_func} but wanted {wanted_func}"
            )


class PluginMeta(type):
    def __new__(cls, name: str, bases: List[type], attrs: Dict[str, Any]):
        plugin_functions = []
        for k, v in attrs.items():
            if k.startswith("_") or not inspect.isfunction(v):
                continue
            plugin_functions.append(plugin_from_function(v, True))
        attrs[f"_{name}__plugin_functions"] = plugin_functions
        return super().__new__(cls, name, bases, attrs)


class Plugin(metaclass=PluginMeta):
    __plugin_functions: List[PluginFunction]
    __module: ModuleType

    def __init__(self, module_path: str):
        spec = il_utils.spec_from_file_location(self.__class__.__name__, module_path)
        mod = il_utils.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _validate_plugin(self.__plugin_functions, mod)
        self.__module = mod

    def after_login(self, name: str, id: int) -> int:
        return self.__module.after_login(name, id)


if __name__ == "__main__":
    plug = Plugin("./plugin_system/plugin_impl.py")
    plug.after_login("user", 12)
