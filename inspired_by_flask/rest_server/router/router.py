from .routing_logics.route_logic import RouteLogic, SimpleRouteLogic
from .routing_logics.routes import Route, SimpleRoute, NestedRoute
from .routing_logics.http_method import HttpMethod
from typing import Any, Callable


class SingletonMeta(type):
    """
    Usage:\n
        class myclass(metaclass = SingletonMeta):
            ...

    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the values of the `__init__` arguments do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class Router(metaclass=SingletonMeta):
    routes: RouteLogic = None

    def __init__(self) -> None:
        self.routes = SimpleRouteLogic()

    def get_handler(
        self, __url: str, method: HttpMethod
    ) -> tuple[Callable, dict | None]:
        """
        get handler for specified __url and method
        if return is Callable,None, the default_handler is returned
        """
        __url_list = __url.split("/")
        return self.routes.get_route(__url_list, method).parse_url(__url_list)

    def add_route(
        self,
        url: str,
        handler: Callable | Route,
        accepted_methods: list[HttpMethod] = [HttpMethod.GET],
        default_params: dict[str, Any] = {},
    ) -> Route:

        new_route = None
        if isinstance(handler, SimpleRoute):
            if not default_params:
                raise ValueError("for NestedRoute default_params are required")
            new_route = NestedRoute(url, handler, set(accepted_methods), default_params)
        elif isinstance(handler, Callable):
            new_route = SimpleRoute(url, handler, set(accepted_methods))
        else:
            raise ValueError(
                f"routing not implemented for handler of type {type(handler)}"
            )

        self.routes.add_route(new_route)
        return new_route

    def route(
        self,
        url: str,
        accepted_methods: list[HttpMethod] = [HttpMethod.GET],
        default_params: dict[str, Any] = {},
    ) -> Route:
        """decorator, same functionality of add_route"""

        def decorate(handler):
            return self.add_route(url, handler, accepted_methods, default_params)

        return decorate


if __name__ == "__main__":
    # testing code
    router = Router(lambda: print("DEFAULT HANDLER"))
    router.add_route(
        "/test/this/url", lambda x: print(f"GET /test/this/url {x}"), [HttpMethod.GET]
    )
    router.add_route(
        "/test/this/url", lambda x: print(f"POST /test/this/url {x}"), [HttpMethod.POST]
    )

    @router.route(
        "/test/<int:this>",
        [HttpMethod.GET, HttpMethod.POST],
        {"url": "bar"},
    )
    @router.route("/test/<int:this>/<url>", [HttpMethod.GET, HttpMethod.POST])
    def oll(this=None, url=None):
        print(f"handler POST/GET parameters {this=}  {url=}")

    handler, params = router.get_handler("/test/this/url", HttpMethod.GET)
    handler(params)
    handler, params = router.get_handler("/test/this/url", HttpMethod.POST)
    handler(params)
    handler, params = router.get_handler("/test/1/foo", HttpMethod.POST)
    handler(**params)
    handler, params = router.get_handler("/test/1", HttpMethod.POST)
    handler(**params)
    handler, params = router.get_handler("/test/shish", HttpMethod.POST)
    assert params is None, "this should be the default handler"
    handler()
    pass
