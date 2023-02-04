from .http_method import HttpMethod
from .routes import Route
from abc import ABC, abstractmethod
from itertools import chain
from copy import copy
import warnings
from typing import List


class RouteNotFoundError(Exception):
    pass


class RouteLogic(ABC):
    @abstractmethod
    def add_route(self, new_route: "Route") -> None:
        """Given a new route save it and map it to get retrieved

        Args:
            new_route (Route): new Route instance with handler and mapped_url setted
        """
        raise NotImplementedError()

    @abstractmethod
    def get_route(self, url: List[str], http_method: "HttpMethod") -> "Route":
        """Given an url and an HttpMethod retrieve the corresponding Route

        Args:
            url (List[str]): url splitted on "/"
            http_method (HttpMethod): method used to call url

        Raises:
            RouteNotFoundError: if route is not found

        Returns:
            Route: mapped Routed to corresponding url and http_method
        """
        raise NotImplementedError()

    @abstractmethod
    def get_definition_and_docstring(self) -> "dict[str,dict[str,str]]":
        """Returns all routed methods definition and descriptions

        Returns:
            dict
        """


class SimpleRouteLogic(RouteLogic):
    # maps url's length to a list of url with that length
    __all_routes = {}  # type: "dict[int, List[Route]]"
    __route_definitions = {}  # type: dict[str,dict[str,str]]

    def __init__(self) -> None:
        super().__init__()

    def add_route(self, new_route: "Route") -> None:
        """Add route to dict mapping its splitted url list's length and appending it to the corresponding list

        Args:
            new_route (Route): new_route to be mapped
        """
        url_length = len(new_route.mapped_url)
        if not self.__all_routes.get(url_length, None):
            self.__all_routes[url_length] = []

        # check if url is alredy mapped
        for route in self.__all_routes[url_length]:
            if route == new_route:
                warnings.warn(
                    "url {} was already mapped and now overriden, care!".format(
                        "/".join(route.mapped_url)
                    )
                )

        self.__all_routes[url_length].append(new_route)

    def get_route(self, url: List[str], http_method: "HttpMethod") -> "Route":
        """Given an url and an HttpMethod retrieve the corresponding Route

        Args:
            url (List[str]): url splitted on "/"
            http_method (HttpMethod): method used to call url

        Raises:
            RouteNotFoundError: if route is not found

        Returns:
            Route: mapped Routed to corresponding url and http_method
        """
        try:
            return next(
                filter(
                    lambda x: x.validate_method(http_method) and x.validate_url(url),
                    self.__all_routes.get(len(url), []),
                )
            )
        except StopIteration as e:
            raise RouteNotFoundError(
                "url: {} and method: {} not routed".format(url, http_method)
            ) from e

    def get_definition_and_docstring(self) -> "dict[str,dict[str,str]]":
        if self.__route_definitions:
            return self.__route_definitions

        for routes in self.__all_routes.values():
            for route in routes:
                self.__route_definitions = {
                    **self.__route_definitions,
                    **route.get_definition_and_docstring(),
                }
        return self.__route_definitions


class RouteNode:
    child_route_nodes = {}  # type: dict[str, "RouteNode"]
    __mapped_routes = {}  # type: dict[HttpMethod, Route]

    def __init__(self, route: "Route" = None) -> None:
        self.child_route_nodes = {}
        self.__mapped_routes = {
            HttpMethod.GET: None,
            HttpMethod.POST: None,
        }

        if route:
            for http_method in route.accepted_methods:
                self.__mapped_routes[http_method] = route

    def set_current_routes(self, route: "Route") -> None:
        """Set current routes to the input route, using as keys the route's accepted_methods parameter

        Args:
            route (Route): route to map in this node
        """
        for http_method in route.accepted_methods:
            if self.__mapped_routes[http_method]:
                warnings.warn(
                    "url {} was already mapped and now overriden, care!".format(
                        "/".join(self.__mapped_routes[http_method].mapped_url)
                    )
                )
            self.__mapped_routes[http_method] = route

    def get_route_nodes_with_url_params(
        self, depth: int, http_method: "HttpMethod"
    ) -> List["RouteNode"]:
        """Search the children of n distance (where one node jump counts as 1) that contains for the requested http_method
        a route that accepts url parameters

        Args:
            depth (int): distance to search the children, if == 0 search is done, return [self]
        Returns:
            List[RouteNode]: list of children node
        """
        if not depth:
            return (
                [self]
                if self.__mapped_routes[http_method]
                and self.__mapped_routes[http_method].has_url_params
                else []
            )
        result = list(
            chain.from_iterable(
                route_node.get_route_nodes_with_url_params(depth - 1, http_method)
                for route_node in self.child_route_nodes.values()
            )
        )
        return result

    def get_route(self, url: List[str], http_method: "HttpMethod") -> "Route":
        """Given an url and an HttpMethod retrieve the corresponding Route

        Args:
            url (List[str]): url splitted on "/"
            http_method (HttpMethod): method used to call url

        Raises:
            RouteNotFoundError: if route is not found

        Returns:
            Route: mapped Routed to corresponding url and http_method
        """
        try:
            result_nodes = self.get_route_node(copy(url), http_method)
        except RouteNotFoundError as route_error:
            raise RouteNotFoundError(
                "url: {} and method: {} not routed".format(url, http_method)
            ) from route_error

        # if a single RouteNode is retreived, return corresponding http_method Route
        if isinstance(result_nodes, RouteNode):
            return result_nodes.__mapped_routes[http_method]

        # if a list of RouteNode is retreived, this means that the url was not directly
        # matched, so we could be searching for an url mapped to accept embedded parameters.
        # Try to find a corresponding url, if not raise RouteNotFoundError
        try:
            return next(
                filter(
                    lambda route: route.validate_url(url),
                    map(
                        lambda route_node: route_node.__mapped_routes[http_method],
                        result_nodes,
                    ),
                )
            )
        except StopIteration as e:
            raise RouteNotFoundError(
                "url: {} and method: {} not routed".format(url, http_method)
            ) from e

    def get_route_node(
        self, url_pieces: List[str], http_method: "HttpMethod"
    ) -> "RouteNode | List[RouteNode]":
        """Given the url_pieces to look for and http_method return a RouteNode or a List of RouteNode.

        If next_url piece is present in child_route_nodes mapping call same method without next_url piece until url_pieces is empty.

        If next_url is not found call get_route_nodes_with_url_params, it will return a List[RouteNode]; see it's __doc__ for more.


        Args:
            url (List[str]): url splitted on "/"
            http_method (HttpMethod): method used to call url

        Raises:
            RouteNotFoundError: if route is not found

        Returns:
            RouteNode | List[RouteNode]: RouteNode if direct mapping found, List[RouteNode] if possibile mapping with parameters to check

        """
        if not url_pieces:
            if self.__mapped_routes[http_method] is None:
                raise RouteNotFoundError("route not found!")
            return self

        next_url = url_pieces.pop(0)
        if next_url not in self.child_route_nodes:
            tmp = []
            for route in self.child_route_nodes.values():
                tmp.extend(
                    route.get_route_nodes_with_url_params(len(url_pieces), http_method)
                )
            return tmp

        return self.child_route_nodes[next_url].get_route_node(url_pieces, http_method)

    def add_route_node(self, url_pieces: List[str], new_route: "Route") -> None:
        """Given the url_pieces to add in the graph and the route, add the route in the required location.

        If next_url piece is not present in child_route_nodes mapping add a new RouteNode,
        then call the same method without next_url piece until url_pieces is empty,
        then map the route to the requested http_methods.

        Args:
            url_pieces (List[str]): list of url pieces missing to map the route
            new_route (Route): new_route to be mapped
        """
        next_url = url_pieces.pop(0)
        # add RouteNode if it doesen't exist
        if next_url not in self.child_route_nodes:
            self.child_route_nodes[next_url] = RouteNode()

        # if not last part of url
        if url_pieces:
            self.child_route_nodes[next_url].add_route_node(url_pieces, new_route)
            return

        self.child_route_nodes[next_url].set_current_routes(new_route)

    def add_route(self, new_route: "Route") -> None:
        """Map a new route in the graph

        Args:
            new_route (Route): route to be mapped
        """
        self.add_route_node(copy(new_route.mapped_url), new_route)

    def get_definition_and_docstring(self) -> "dict[str,dict[str,str]]":
        out_defs = {}
        for route in self.child_route_nodes.values():
            out_defs = {**out_defs, **route.get_definition_and_docstring()}
        for method in HttpMethod:
            if self.__mapped_routes[method]:
                out_defs = {
                    **out_defs,
                    **self.__mapped_routes[method].get_definition_and_docstring(),
                }
        return out_defs


class GraphRouteLogic(RouteLogic):
    __all_routes = None  # type: RouteNode
    __route_definitions = {}  # type: dict[str,dict[str,str]]

    def __init__(self) -> None:
        self.__all_routes = RouteNode()
        self.__route_definitions = {}

    def add_route(self, new_route: "Route") -> None:
        """Add route to the graph mapping adding the corresponding nodes
        Args:
            new_route (Route): new_route to be mapped
        """

        self.__all_routes.add_route(new_route)

    def get_route(self, url: List[str], http_method: "HttpMethod") -> "Route":
        """Given an url and an HttpMethod retrieve the corresponding Route

        Args:
            url (List[str]): url splitted on "/"
            http_method (HttpMethod): method used to call url

        Raises:
            RouteNotFoundError: if route is not found

        Returns:
            Route: mapped Routed to corresponding url and http_method
        """
        return self.__all_routes.get_route(url, http_method)

    def get_definition_and_docstring(self) -> dict[str, dict[str, str]]:
        if self.__route_definitions:
            return self.__route_definitions

        self.__route_definitions = self.__all_routes.get_definition_and_docstring()
        return self.__route_definitions
