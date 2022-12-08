from .http_method import HttpMethod
from .routes import Route


class RouteSet:
    # maps url's length to a list of url with that length
    __all_routes: "dict[int, list[Route]]" = {}

    def add_route(self, new_route: "Route") -> bool:
        url_length = len(new_route.mapped_url)
        if not self.__all_routes.get(url_length, None):
            self.__all_routes[url_length] = []

        # check if url is alredy mapped
        for route in self.__all_routes[url_length]:
            if route == new_route:
                return False

        self.__all_routes[url_length].append(new_route)
        return True

    def get_route(self, __url: list[str], method: "HttpMethod") -> "Route":
        return next(
            filter(
                lambda x: x.validate_method(method) and x.validate_url(__url),
                self.__all_routes.get(len(__url), []),
            )
        )
