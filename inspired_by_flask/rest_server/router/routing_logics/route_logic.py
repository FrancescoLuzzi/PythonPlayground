from .http_method import HttpMethod
from .routes import Route
from abc import ABC, abstractmethod


class RouteNotFoundError(Exception):
    pass


class RouteLogic(ABC):
    @abstractmethod
    def add_route(self, new_route: "Route") -> bool:
        """Given a new route save it and map it to get retrived

        Args:
            new_route (Route): Route instance

        Returns:
            bool: if the operation went good or not
        """
        raise NotImplementedError()

    @abstractmethod
    def get_route(self, url: list[str], method: "HttpMethod") -> "Route":
        """Given an url and an HttpMethod retrieve the corresponding Route

        Args:
            url (list[str]): url splitted on "/"
            method (HttpMethod): method used to call __url

        Raises:
            StopIteration: if

        Returns:
            Route:
        """
        raise NotImplementedError()


class SimpleRouteLogic(RouteLogic):
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

    def get_route(self, url: list[str], method: "HttpMethod") -> "Route":
        try:
            return next(
                filter(
                    lambda x: x.validate_method(method) and x.validate_url(url),
                    self.__all_routes.get(len(url), []),
                )
            )
        except StopIteration as e:
            raise RouteNotFoundError(
                f"url: {url} and method: {method} not routed"
            ) from e
