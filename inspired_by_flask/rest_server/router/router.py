from .routing_logics.route_logic import RouteLogic, SimpleRouteLogic, GraphRouteLogic
from .routing_logics.routes import Route, SimpleRoute, NestedRoute, url_split
from .routing_logics.http_method import HttpMethod
from typing import Any, Callable, List, Optional, Union, Tuple


class NamedSingletonMeta(type):
    """
    Usage:\n
        class myclass(metaclass = NamedSingletonMeta):
            ...

    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the values of the `__init__` arguments do not affect
        the returned instance.
        Classes that uses this Metaclass needs a kw parameter called "instance_name" to be able to get
        that instance.
        """
        instance_name = kwargs.get("instance_name", None)
        if instance_name and instance_name not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[instance_name] = instance
        return cls._instances[instance_name]


class Router(metaclass=NamedSingletonMeta):
    routes = None  # type: RouteLogic

    def __init__(self, *, instance_name: str) -> None:
        self.instance_name = instance_name
        self.routes = GraphRouteLogic()

    def get_handler(
        self, __url: str, method: "HttpMethod"
    ) -> Tuple[Callable, Optional[dict]]:
        """
        get handler for specified __url and method
        if return is Callable,None, the default_handler is returned
        """
        __url_list = url_split(__url)
        return self.routes.get_route(__url_list, method).parse_url(__url_list)

    def add_route(
        self,
        url: str,
        handler: Union[Callable, "Route"],
        accepted_methods: List["HttpMethod"] = [HttpMethod.GET],
        default_params: dict[str, Any] = {},
    ) -> "Route":

        new_route = None
        if isinstance(handler, SimpleRoute):
            if not default_params:
                raise ValueError("for NestedRoute default_params are required")
            if not handler.has_url_params:
                raise ValueError(
                    "for NestedRoute the nested Route needs to have url params"
                )
            new_route = NestedRoute(url, handler, set(accepted_methods), default_params)
        elif isinstance(handler, Callable):
            new_route = SimpleRoute(url, handler, set(accepted_methods))
        else:
            raise ValueError(
                "routing not implemented for handler of type {}".format(type(handler))
            )

        self.routes.add_route(new_route)
        return new_route

    def route(
        self,
        url: str,
        accepted_methods: List["HttpMethod"] = [HttpMethod.GET],
        default_params: dict[str, Any] = {},
    ) -> "Route":
        """decorator, same functionality of add_route"""

        def decorate(handler):
            return self.add_route(url, handler, accepted_methods, default_params)

        return decorate

    def get_definition_and_docstring(self) -> "dict[str,dict[str,str]]":
        return self.routes.get_definition_and_docstring()


if __name__ == "__main__":
    # testing code
    from time import time

    router = Router()
    router.add_route(
        "/test/this/url",
        lambda x: print("GET /test/this/url {}".format(x)),
        [HttpMethod.GET],
    )
    router.add_route(
        "/test/this/url",
        lambda x: print("POST /test/this/url {}".format(x)),
        [HttpMethod.POST],
    )

    @router.route(
        "/test/<int:this>",
        [HttpMethod.GET, HttpMethod.POST],
        {"url": "bar"},
    )
    @router.route("/test/<int:this>/<url>", [HttpMethod.GET, HttpMethod.POST])
    def oll(this=None, url=None):
        print("handler POST/GET parameters this={}  url={}".format(this, url))

    handler, params = router.get_handler("/test/this/url", HttpMethod.GET)
    handler(params)
    handler, params = router.get_handler("/test/this/url", HttpMethod.POST)
    handler(params)
    handler, params = router.get_handler("/test/1/foo", HttpMethod.POST)
    handler(**params)
    handler, params = router.get_handler("/test/1", HttpMethod.POST)
    handler(**params)
    try:
        handler, params = router.get_handler("/test/shish", HttpMethod.POST)
    except Exception:
        print("this route doesn't exists")
    start = time()

    class TestClass:
        def __init__(self, i: int) -> None:
            self.i = i
            router.add_route(
                "/test/this/url/{}".format(i),
                self.get_print_self,
                [HttpMethod.GET],
            )

        def get_print_self(self):
            print("GET/test/this/url/{}".format(self.i))

    objects_list = []
    for i in range(5 * 10**3):
        objects_list.append(TestClass(i))

    def print_name(*, name: str):
        print("GET /test/this/url {}".format(name))

    router.add_route(
        "/test/this/url/<name>",
        print_name,
        [HttpMethod.GET],
    )
    # with GraphRouteLogic 0.0491 seconds
    # with SimpleRouteLogic 5.1876 seconds
    print("time elapsed: {}".format(time() - start))
    start = time()
    handler, params = router.get_handler("/test/this/url/suck", HttpMethod.GET)
    handler(**params)
    handler, _ = router.get_handler("/test/this/url/3647", HttpMethod.GET)
    handler()
    # with GraphRouteLogic 0.0079 seconds
    # with SimpleRouteLogic 0.0173 seconds
    print("time elapsed: {}".format(time() - start))
