from http_utils import HttpMethod
from typing import Any, Generic, TypeVar, Callable
from re import compile
from collections import defaultdict

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


def parse_url(url_format: str, url: str) -> dict[str, str]:
    """
    from format /url/format/<int:name1>/<name2>
    url="/url/format/1/oh_yeah" -> return {"name1": "1", "name2": "oh_yeah"}
    url="/url/format/1" -> raise UrlFormatError("url missformatted")
    """
    params_dict = {}
    url_format_list = url_format.split("/")
    url_list = url.split("/")
    if len(url_format_list) != len(url_list):
        raise UrlFormatError(f"len of format url is different from given url")

    for format_part, request_part in zip(url_format_list, url_list):
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
    parsers_dict = {}
    for param in _URL_PARAMS_FINDER.findall(url_format):

        param = _URL_PARAMS_TYPE_FINDER.match(param)
        param_type = param.group("type") if param is not None else "str"
        param_type = _PARAM_TYPE_MAPPER[param_type]
        parsers_dict[param.group("name")] = UrlParamFormatter[param_type](param_type)
    return parsers_dict


class Route:
    mapped_url: str = ""
    handler: Callable = print
    accepted_methods: list[HttpMethod] = []
    __reqired_url_params: dict[str, UrlParamFormatter] = {}
    __default_url_params: dict[str, Any] = {}

    def __init__(
        self,
        url: str,
        handler: Callable,
        accepted_methods: list[HttpMethod],
        default_url_params: dict[str, Any] = {},
    ) -> None:
        self.mapped_url = url
        self.accepted_methods = accepted_methods
        self.__default_url_params = default_url_params
        self.__reqired_url_params = from_url_get_required_params(url)
        self.handler = handler

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, self.__class__):
            return (
                self.mapped_url == __o.mapped_url
                and self.accepted_methods == __o.accepted_methods
            )
        else:
            raise ValueError(f"== not supported for type {type(__o)}")

    def validate_method(self, method: HttpMethod):
        return method in self.accepted_methods

    def validate_url(self, url: str) -> bool:
        try:
            return all(
                self.__reqired_url_params[key].is_convertable(value)
                for key, value in parse_url(self.mapped_url, url).items()
            )
        except UrlFormatError:
            return False

    def parse_url(self, url: "str") -> tuple[Callable, dict]:
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
        handler: Callable,
    ) -> None:
        super().__init__(url, handler, [], {})

    def parse_url(self, url: "str") -> tuple[Callable, dict]:
        return self.handler, {}


class RoutesSet:
    __all_routes: list[Route] = []
    __default_route: DefaultRoute = None

    def __init__(self, default_route: DefaultRoute) -> None:
        self.__default_route = default_route

    def add_route(self, new_route: Route) -> bool:
        for route in self.__all_routes:
            if route == new_route:
                return False

        self.__all_routes.append(new_route)
        return True

    def get_route(self, __url: str, method: HttpMethod) -> Route:
        return next(
            filter(
                lambda x: x.validate_method(method) and x.validate_url(__url),
                self.__all_routes,
            ),
            self.__default_route,
        ).parse_url(__url)


class Router:
    routes: RoutesSet = None

    def __init__(self, default_handler: Callable) -> None:
        self.routes = RoutesSet(DefaultRoute("", default_handler))

    def get_handler(self, __url: str, method: HttpMethod) -> tuple[Callable, dict]:
        return self.routes.get_route(__url, method).parse_url(__url)

    def route(
        self,
        url: str,
        handler: Callable,
        accepted_methods: list[HttpMethod] = [HttpMethod.GET],
        default_params: dict[str, Any] = {},
    ):
        self.routes.add_route(Route(url, handler, accepted_methods, default_params))


if __name__ == "__main__":
    # testing code
    pass
