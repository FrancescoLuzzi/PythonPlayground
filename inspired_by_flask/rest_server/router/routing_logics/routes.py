from abc import ABC, abstractmethod
from collections import defaultdict
from functools import update_wrapper
from re import compile
import logging
from typing import (
    Any,
    List,
    Callable,
    Generic,
    Iterator,
    TypeVar,
    Tuple,
    get_type_hints,
)
from inspect import getdoc

from .http_method import HttpMethod

_LOGGER = logging.getLogger(__name__)

_URL_PARAMS_FINDER = compile(r"(\<.+?\>)")
_URL_PARAMS_TYPE_FINDER = compile(r"\<((?P<type>.+):)?(?P<name>.+){1}\>")
_PARAM_TYPE_MAPPER = defaultdict(lambda: str, {"int": int, "float": float})
"""
>>> oll = _URL_PARAMS_FINDER.findall("/url/format/<int:name1>/<name2>")
>>> oll
['<int:name1>', '<name2>']
>>> param = _URL_PARAMS_TYPE_FINDER.match(oll[0])
>>> param.group("type")
'int'
"""

T = TypeVar("T")


class UrlFormatError(ValueError):
    pass


class UrlParamFormatter(Generic[T]):
    converter: T = None

    def __init__(self, converter: T) -> None:
        self.converter = converter

    def is_convertable(self, value: str) -> bool:
        try:
            self.convert(value)
            return True
        except ValueError:
            return False

    def convert(self, value: str) -> T:
        return self.converter(value)


def url_split(url: str) -> List[str]:
    """Split url string removing the first substring

    ES:
        url_split("/") -> ""
        url_split("") -> ""
        url_split("/test") -> "test"

    Args:
        url (str): string separated by "/"

    Returns:
        List[str]: splitted string on "/"
    """
    output = url.split("/")
    return output[1:] if len(output) > 1 else output


def parse_url(url_format: List[str], url: List[str]) -> dict[str, str]:
    """
    from format /url/format/<int:name1>/<name2> passed as ["url","format","<int:name1>","<name2>"]
    url=["url","format","1","oh_yeah"] -> return {"name1": "1", "name2": "oh_yeah"}
    url=["url","format","1"] -> raise UrlFormatError("url missformatted")
    """
    params_dict = {}
    if len(url_format) != len(url):
        raise UrlFormatError(
            "len of format url is different from given url\nurl_format={}\nurl={}".format(
                url_format, url
            )
        )

    for format_part, request_part in zip(url_format, url):
        if format_part == request_part:
            continue
        param = _URL_PARAMS_TYPE_FINDER.match(format_part)
        if not param:
            raise UrlFormatError(
                "part of the path of the url was different and wasn't a param"
            )
        params_dict[param.group("name")] = request_part
    return params_dict


def from_url_get_required_params(url_format: str) -> dict[str, "UrlParamFormatter"]:
    """
    from format /url/format/<int:name1>/<name2>

    return {"name1": UrlParamFormatter[int], "name2": UrlParamFormatter[str]}
    """
    params_formatters = {}
    for param in _URL_PARAMS_FINDER.findall(url_format):
        param = _URL_PARAMS_TYPE_FINDER.match(param)
        param_type = param.group("type") if param is not None else "str"
        param_type = _PARAM_TYPE_MAPPER[param_type]
        params_formatters[param.group("name")] = UrlParamFormatter[param_type](
            param_type
        )
    return params_formatters


def url_contains_params(url_format: str) -> bool:
    """
    from format /url/format/<int:name1>/<name2>

    return True
    """
    return bool(_URL_PARAMS_FINDER.findall(url_format))


def from_url_get_required_params_names(url_format: List[str]) -> Iterator[str]:
    """
    from format ["url","format","<int:name1>","<name2>"]
    return Iterator("name1","name2")
    """
    for param in url_format:
        param = _URL_PARAMS_TYPE_FINDER.match(param)
        if not param:
            continue
        yield param.group("name")


def remove_quotes(string: str):
    return "".join(filter(lambda x: x not in ['"', "'"], string))


class Route(ABC):
    mapped_url = []  # type:List[str]
    accepted_methods = []  # type: set["HttpMethod"]

    @abstractmethod
    def __init__(self) -> None:
        raise NotImplementedError()

    def __eq__(self, __o: object) -> bool:
        if issubclass(__o.__class__, Route):
            return (
                self.mapped_url == __o.mapped_url
                and self.accepted_methods & __o.accepted_methods
            )
        else:
            raise ValueError("== not supported for type {}".format(type(__o)))

    def validate_method(self, method: "HttpMethod"):
        return method in self.accepted_methods

    @property
    @abstractmethod
    def has_url_params(self):
        raise NotImplementedError()

    @abstractmethod
    def validate_url(self, url: List[str]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def parse_url(self, url: List[str]) -> Tuple[Callable, dict]:
        raise NotImplementedError()

    @abstractmethod
    def get_definition_and_docstring(self) -> dict:
        raise NotImplementedError()


class SimpleRoute(Route):
    handler = print  # type: Callable
    __reqired_url_params = {}  # type: dict[str, "UrlParamFormatter"]
    definition_and_docstring = {}  # type: dict[str,dict[str,str]]

    def __init__(
        self,
        url: str,
        handler: Callable,
        accepted_methods: set["HttpMethod"],
    ) -> None:
        self.mapped_url = url_split(url)
        self.accepted_methods = accepted_methods
        self.__reqired_url_params = from_url_get_required_params(url)
        self.handler = handler
        self.definition_and_docstring = {}
        route_infos = {}
        route_infos["description"] = getdoc(handler)
        handler_type_hints = {
            key: remove_quotes(str(value))
            for key, value in get_type_hints(handler).items()
        }
        route_infos["return"] = handler_type_hints.get("return")
        try:
            del handler_type_hints["return"]
        except KeyError:
            _LOGGER.warning(
                "function %s, routed to url %s, doesn't have a return type hint!",
                handler.__name__,
                url,
            )
        route_infos["parameters"] = handler_type_hints
        methods_to_str = "_".join(map(str, accepted_methods))
        self.definition_and_docstring[" ".join((methods_to_str, url))] = route_infos
        update_wrapper(wrapper=self, wrapped=self.handler)

    @property
    def has_url_params(self) -> bool:
        return bool(self.__reqired_url_params)

    def validate_url(self, url: List[str]) -> bool:
        try:
            return all(
                self.__reqired_url_params[key].is_convertable(value)
                for key, value in parse_url(self.mapped_url, url).items()
            )
        except UrlFormatError:
            return False

    def parse_url(self, url: List[str]) -> Tuple[Callable, dict]:
        return (
            self.handler,
            {
                key: self.__reqired_url_params[key].convert(value)
                for key, value in parse_url(self.mapped_url, url).items()
            },
        )

    def get_definition_and_docstring(self) -> "dict[str,dict[str,str]]":
        return self.definition_and_docstring

    def __call__(self, *args, **kwargs) -> Any:
        return self.handler(*args, **kwargs)


class NestedRoute(Route):
    mapped_route = None  # type: Route
    __default_url_params_str = []  # type: List[str]

    def __init__(
        self,
        url: str,
        mapped_route: "SimpleRoute",
        accepted_methods: set["HttpMethod"],
        default_url_params: dict[str, Any],
    ) -> None:
        self.mapped_url = url_split(url)
        self.accepted_methods = accepted_methods
        # extract url params names in order so we can append in the url
        # the default values in the correct order
        self.mapped_route = mapped_route
        self.__default_url_params_str = [
            str(default_url_params[param_name])
            for param_name in from_url_get_required_params_names(
                self.mapped_route.mapped_url
            )
            if param_name in default_url_params
        ]
        try:
            mapped_route_url = next(iter(mapped_route.get_definition_and_docstring()))
            mapped_route.definition_and_docstring[mapped_route_url][
                "default"
            ] = default_url_params
        except StopIteration:
            # empty description
            _LOGGER.warning(
                "{} has empty definition!".format("/".join(mapped_route.mapped_url))
            )
        update_wrapper(wrapper=self, wrapped=self.mapped_route.handler)

    @property
    def has_url_params(self) -> bool:
        return True

    def validate_url(self, url: List[str]) -> bool:
        return self.mapped_route.validate_url(url + self.__default_url_params_str)

    def parse_url(self, url: List[str]) -> Tuple[Callable, dict]:
        return self.mapped_route.parse_url(url + self.__default_url_params_str)

    def get_definition_and_docstring(self) -> "dict[str,dict[str,str]]":
        return {}

    def __call__(self, *args, **kwargs) -> Any:
        return self.mapped_route(*args, **kwargs)
