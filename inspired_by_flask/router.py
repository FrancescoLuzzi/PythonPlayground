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


# url_format /url/format/<type_var:name1>/<name2>
# name1 will be converted as type type_var
# name2 will be defaulted to str


def parse_url(url_format: str, url: str) -> dict[str]:
    """
    from format /url/format/<int:name1>/<name2>
    url="/url/format/1/oh_yeah" -> return {"name1": "1", "name2": "oh_yeah"}
    url="/url/format/1" -> raise UrlFormatError("url missformatted")
    """
    pass


def from_url_get_required_params(url_format: str) -> dict[UrlParamFormatter]:
    """
    from format /url/format/<int:name1>/<name2>
    url="/url/format/1/oh_yeah" -> return {"name1": UrlParamFormatter[int], "name2": UrlParamFormatter[str]}
    """
    pass


class Route:
    mapped_url: str = ""
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
        self.mapped_url = url
        self.accepted_methods = accepted_methods
        self.__default_url_params = default_url_params
        self.__reqired_url_params = from_url_get_required_params(url)
        self.handler = handler

    def validate_url(self, url: str) -> bool:
        try:
            return all(
                self.__reqired_url_params[key].is_convertable(value)
                for key, value in parse_url(self.mapped_url, url).items()
            )
        except UrlFormatError:
            return False

    def parse_url(self, url: "str") -> tuple[function, dict]:
        return (
            self.handler,
            {
                **self.__default_url_params,
                **{
                    key: self.__reqired_url_params[key].convert(value)
                    for key, value in parse_url(self.mapped_url, url).items()
                },
            },
        )


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
