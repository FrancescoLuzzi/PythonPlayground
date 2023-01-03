from .http_method import HttpMethod
from .routes import Route
from abc import ABC, abstractmethod
from itertools import chain
from copy import copy
import warnings


class RouteNotFoundError(Exception):
    pass


class RouteLogic(ABC):
    @abstractmethod
    def add_route(self, new_route: "Route") -> None:
        """Given a new route save it and map it to get retrived

        Args:
            new_route (Route): new Route instance with handler and mapped_url setted
        """
        raise NotImplementedError()

    @abstractmethod
    def get_route(self, url: list[str], http_method: "HttpMethod") -> "Route":
        """Given an url and an HttpMethod retrieve the corresponding Route

        Args:
            url (list[str]): url splitted on "/"
            method (HttpMethod): method used to call url

        Raises:
            RouteNotFoundError: if route is not found

        Returns:
            Route: mapped Routed to corresponding url and http_method
        """
        raise NotImplementedError()


class SimpleRouteLogic(RouteLogic):
    # maps url's length to a list of url with that length
    __all_routes: "dict[int, list[Route]]" = {}

    def add_route(self, new_route: "Route") -> None:
        """Add route to dict mapping its splitted url list's length and appending it to the corresponding list

        Args:
            new_route (Route): new_route to be routed
        """
        url_length = len(new_route.mapped_url)
        if not self.__all_routes.get(url_length, None):
            self.__all_routes[url_length] = []

        # check if url is alredy mapped
        for route in self.__all_routes[url_length]:
            if route == new_route:
                warnings.warn(
                    f"url {'/'.join(route.mapped_url)} was already mapped and now overriden, care!"
                )

        self.__all_routes[url_length].append(new_route)

    def get_route(self, url: list[str], http_method: "HttpMethod") -> "Route":
        try:
            return next(
                filter(
                    lambda x: x.validate_method(http_method) and x.validate_url(url),
                    self.__all_routes.get(len(url), []),
                )
            )
        except StopIteration as e:
            raise RouteNotFoundError(
                f"url: {url} and method: {http_method} not routed"
            ) from e


class RouteNode:
    next_routes: dict[str, "RouteNode"] = None
    current_routes: dict[HttpMethod, Route] = None

    def __init__(self, route: Route = None) -> None:
        self.next_routes = {}
        self.current_routes = {
            HttpMethod.GET: None,
            HttpMethod.POST: None,
        }

        if route:
            for http_method in route.accepted_methods:
                self.current_routes[http_method] = route

    def set_current_routes(self, route: Route) -> None:
        for http_method in route.accepted_methods:
            if self.current_routes[http_method]:
                warnings.warn(
                    f"url {'/'.join(self.current_routes[http_method].mapped_url)} was already mapped and now overriden, care!"
                )
            self.current_routes[http_method] = route

    def get_route_nodes_with_url_params(self, depth: int) -> list["RouteNode"]:
        if not depth:
            return (
                [self]
                if any(x and x.has_url_params for x in self.current_routes.values())
                else []
            )
        result = list(
            chain.from_iterable(
                route_node.get_route_nodes_with_url_params(depth - 1)
                for route_node in self.next_routes.values()
            )
        )
        return result

    def get_route_node(
        self, url_pieces: list[str], http_method: HttpMethod
    ) -> "RouteNode | list[RouteNode]":
        if not url_pieces:
            if self.current_routes[http_method] is None:
                raise RouteNotFoundError("route not found!")
            return self

        curr_url = url_pieces.pop(0)
        if curr_url not in self.next_routes:
            tmp = []
            for route in self.next_routes.values():
                tmp.extend(route.get_route_nodes_with_url_params(len(url_pieces)))
            return tmp

        return self.next_routes[curr_url].get_route_node(url_pieces, http_method)

    def add_route_node(self, url_pieces: list[str], route: Route) -> None:
        curr_url = url_pieces.pop(0)
        # add RouteNode if it doesen't exist
        if curr_url not in self.next_routes:
            self.next_routes[curr_url] = RouteNode()

        # if not last part of url
        if url_pieces:
            self.next_routes[curr_url].add_route_node(url_pieces, route)
            return

        self.next_routes[curr_url].set_current_routes(route)


class GraphRouteLogic(RouteLogic):
    __all_routes: RouteNode = None

    def __init__(self) -> None:
        self.__all_routes = RouteNode()

    def add_route(self, new_route: "Route") -> None:
        self.__all_routes.add_route_node(copy(new_route.mapped_url), new_route)

    def get_route(self, url: list[str], http_method: "HttpMethod") -> "Route":
        try:
            result = self.__all_routes.get_route_node(copy(url), http_method)
        except RouteNotFoundError as route_error:
            raise RouteNotFoundError(
                f"url: {url} and method: {http_method} not routed"
            ) from route_error

        # return RouteNode Route
        if isinstance(result, RouteNode):
            return result.current_routes[http_method]

        try:
            return next(
                filter(
                    lambda x: x and x.validate_url(url),
                    map(lambda x: x.current_routes[http_method], result),
                )
            )
        except StopIteration as e:
            raise RouteNotFoundError(
                f"url: {url} and method: {http_method} not routed"
            ) from e
