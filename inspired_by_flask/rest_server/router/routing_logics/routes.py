from abc import ABC, abstractmethod
from collections import defaultdict
from functools import update_wrapper
from re import compile
from typing import Any, Callable, Generic, Iterator, TypeVar

from .http_method import HttpMethod

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


class RouteNotFoundError(Exception):
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


def parse_url(url_format: list[str], url: list[str]) -> dict[str, str]:
    """
    from format /url/format/<int:name1>/<name2> passed as ["url","format","<int:name1>","<name2>"]
    url=["url","format","1","oh_yeah"] -> return {"name1": "1", "name2": "oh_yeah"}
    url=["url","format","1"] -> raise UrlFormatError("url missformatted")
    """
    params_dict = {}
    if len(url_format) != len(url):
        raise UrlFormatError(f"len of format url is different from given url")

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


def from_url_get_required_params(url_format: str) -> dict[str, UrlParamFormatter]:
    """
    from format /url/format/<int:name1>/<name2>
    url="/url/format/1/oh_yeah" -> return {"name1": UrlParamFormatter[int], "name2": UrlParamFormatter[str]}
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


def from_url_get_required_params_names(url_format: list[str]) -> Iterator[str]:
    """
    from format ["url","format","<int:name1>","<name2>"]
    return Iterator("name1","name2")
    """
    for param in url_format:
        param = _URL_PARAMS_TYPE_FINDER.match(param)
        if not param:
            continue
        yield param.group("name")


class Route(ABC):
    mapped_url: list[str] = []
    accepted_methods: set["HttpMethod"] = []

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
            raise ValueError(f"== not supported for type {type(__o)}")

    def validate_method(self, method: "HttpMethod"):
        return method in self.accepted_methods

    @abstractmethod
    def validate_url(self, url: list[str]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def parse_url(self, url: list[str]) -> tuple[Callable, dict]:
        raise NotImplementedError()


class SimpleRoute(Route):
    handler: Callable = print
    __reqired_url_params: dict[str, UrlParamFormatter] = {}

    def __init__(
        self,
        url: str,
        handler: Callable,
        accepted_methods: set["HttpMethod"],
    ) -> None:
        self.mapped_url = url.split("/")
        self.accepted_methods = accepted_methods
        self.__reqired_url_params = from_url_get_required_params(url)
        self.handler = handler
        update_wrapper(wrapper=self, wrapped=self.handler)

    def validate_url(self, url: list[str]) -> bool:
        try:
            return all(
                self.__reqired_url_params[key].is_convertable(value)
                for key, value in parse_url(self.mapped_url, url).items()
            )
        except UrlFormatError:
            return False

    def parse_url(self, url: list[str]) -> tuple[Callable, dict]:
        return (
            self.handler,
            {
                key: self.__reqired_url_params[key].convert(value)
                for key, value in parse_url(self.mapped_url, url).items()
            },
        )

    def __call__(self, *args, **kwargs) -> Any:
        return self.handler(*args, **kwargs)


class NestedRoute(Route):
    mapped_route: Route
    __default_url_params_str: list[str] = []

    def __init__(
        self,
        url: str,
        mapped_route: SimpleRoute,
        accepted_methods: set["HttpMethod"],
        default_url_params: dict[str, Any],
    ) -> None:
        self.mapped_url = url.split("/")
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
        update_wrapper(wrapper=self, wrapped=self.mapped_route.handler)

    def validate_url(self, url: list[str]) -> bool:
        return self.mapped_route.validate_url(url + self.__default_url_params_str)

    def parse_url(self, url: list[str]) -> tuple[Callable, dict]:
        return self.mapped_route.parse_url(url + self.__default_url_params_str)

    def __call__(self, *args, **kwargs) -> Any:
        return self.mapped_route(*args, **kwargs)
