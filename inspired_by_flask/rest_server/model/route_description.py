from rest_server.router.routing_logics.http_method import HttpMethod
from typing import Any
from http import HTTPStatus

# for reference https://swagger.io/docs/specification/2-0/describing-parameters/

DEFAULT_RETURN_VALUES = [
    HTTPStatus.OK,
    HTTPStatus.BAD_REQUEST,
    HTTPStatus.INTERNAL_SERVER_ERROR,
]


def change_path_params_format(path: str) -> str:
    out_url_pieces = []
    for piece in path.split("/"):
        if "<" in piece:
            if ":" in piece:
                piece = "{" + piece.split(":")[1]
            else:
                piece = piece.replace("<", "{")
            piece = piece.replace(">", "}")
        out_url_pieces.append(piece)
    return "/".join(out_url_pieces)


def merge_swagger_outputs(*args: "tuple[RouteDefinition]") -> dict:
    """Merge swagger json if RouteDefinition are of the same path but different HttpMethod usage

    Raises:
            ValueError: if any of the provided elements are not of type RouteDefinition

    Returns:
        dict: merged swagger dict definition
    """
    if any(not isinstance(x, RouteDefinition) for x in args):
        raise ValueError(
            "some of the provided elements are not of type RouteDefinition"
        )
    path = args[0].path
    output = {path: {}}

    for route_def in args:
        output[path] = route_def.to_swager()[path]
    return output


class RouteParam:
    name = ""  # type:str
    type = ""  # type:str
    default_value = None  # type:Any
    is_required = True  # type:bool

    def __init__(self, name: str, type: str) -> None:
        self.name = name
        self.type = type


class RouteDefinition:
    path = ""  # type: str
    description = ""  # type:str
    methods = []  # type: list[HttpMethod]
    path_params = {}  # type: list[RouteParam]
    params = {}  # type: list[RouteParam]
    return_types = ""  # type:list[HTTPStatus]

    def __init__(
        self,
        path: str,
        description: str,
        methods: "list[HttpMethod]",
        path_params: "list[RouteParam]",
        params: "list[RouteParam]",
        return_types: "list[HTTPStatus]" = DEFAULT_RETURN_VALUES,
    ) -> None:
        self.path = change_path_params_format(path)
        self.description = description
        self.methods = methods
        self.path_params = path_params
        self.params = params
        self.return_types = return_types

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, RouteDefinition):
            return self.path == __o.path and self.methods == __o.methods
        raise ValueError("__eq__ not implemented for type {}".format(type(__o)))

    def __get_params_swagger(self) -> "list[dict]":
        pass

    def __get_path_params_swagger(self) -> "list[dict]":
        pass

    def add_default_to_path_param(
        self, path_param_name: str, default_value: Any
    ) -> None:
        for path_param in self.path_params:
            if path_param.name == path_param_name:
                path_param.default_value = default_value
                break

    def to_swager(self) -> dict:
        output = {self.path: {}}
        for method in self.methods:
            output[self.path][str(method)] = {}
            output[self.path][str(method)]["summary"] = self.description
            output[self.path][str(method)]["params"] = self.description
