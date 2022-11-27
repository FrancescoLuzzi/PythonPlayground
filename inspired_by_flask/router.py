from http_utils import HttpMethod
from typing import Any, Generic, TypeVar
from re import compile

_URL_PARAMS_FINDER = compile(r"(\<.+?\>)")
_URL_PARAMS_TYPE_FINDER = compile(r"\<((?P<type>.+):)?(?P<name>.+){1}\>")
"""
>>> oll = _URL_PARAMS_FINDER.findall("/url/format/<int:name1>/<name2>")
>>> oll
['<int:name1>', '<name2>']
>>> param = _URL_PARAMS_TYPE_FINDER.match(oll[0])
>>> param.group("type")
'int'
"""

T = TypeVar("T")


class UrlParamFormatter(Generic[T]):
    converter: T = None

    def __init__(self, converter: T) -> None:
        self.converter = converter

    def convert(self, value: str) -> T:
        return self.convert(value)


# url_format /url/format/<type_var:name1>/<name2>
# name1 will be converted as type type_var
# name2 will be defaulted to str


def url_parser(url_format: str, url: str) -> dict[Any]:
    pass


def from_url_get_required_params(url_format: str) -> dict[UrlParamFormatter]:
    pass


class Route:
    url: str = ""
    handler: function = print
    accepted_methods: list[HttpMethod] = []
    __reqired_url_params: dict[str, UrlParamFormatter] = {}
    __default_url_params: dict[str, Any] = {}

    def __init__(
        self,
        url: str,
        handler: function,
        accepted_methods: list[HttpMethod],
        default_url_params: dict[str, Any] = {},
    ) -> None:
        self.url = url
        self.accepted_methods = accepted_methods
        self.__default_url_params = default_url_params
        self.__reqired_url_params = from_url_get_required_params(url)
        self.handler = handler

    def validate_url(self, url: str) -> bool:
        pass

    def parse_url(self, url: "str") -> tuple[function, dict]:
        pass


class DefaultRoute(Route):
    def __init__(
        self,
        url: str,
        handler: function,
    ) -> None:
        super().__init__(url, handler, [], {})

    def parse_url(self, url: "str"):
        return self.handler, {}


class Router:
    routes: set[Route] = set()
    __default_route: Route

    def __init__(self, default_handler: function) -> None:
        self.__default_route = DefaultRoute("", default_handler)

    def __getattribute__(self, __url: str) -> tuple[function, dict]:
        return next(
            filter(lambda x: x.validate(__url), self.routes), self.__default_route
        ).parse_url(__url)
