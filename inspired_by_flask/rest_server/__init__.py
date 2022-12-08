from os import environ
import logging
import socketserver
import json
from http.server import BaseHTTPRequestHandler
from typing import Any
from http import HTTPStatus
from urllib.parse import parse_qs, urlparse
from .router import Router, RouteNotFoundError
from .router import HttpMethod


_LOGGER = logging.getLogger(__name__)
_FAVICO_CONTENT = b""
try:
    with open(environ.get("FAVICO_PATH", ""), "rb") as favicon_file:
        _FAVICO_CONTENT = favicon_file.read()
except FileNotFoundError:
    _favicon_path = environ.get("FAVICO_PATH", "FAVICO_PATH not set in os.environ")
    _LOGGER.warning(f"favico file not found -> {_favicon_path}")


class RestWebserver(BaseHTTPRequestHandler):
    def __init__(
        self,
        request: bytes,
        client_address: tuple[str, int],
        server: socketserver.BaseServer,
    ) -> None:
        super().__init__(request, client_address, server)

    def __default_func(self, *, HttpMethod_type: HttpMethod = None, **kwargs):
        """
        Default return when an url is not mapped to a function
        """
        self.__send_headers(HTTPStatus.NOT_IMPLEMENTED)
        _LOGGER.warning(f"{self.path} request not mapped for {HttpMethod_type} method.")

    def log_message(self, format: str, *args) -> None:
        _LOGGER.info("%s - - %s\n" % (self.address_string(), format % args))

    def log_error(self, format: str, *args) -> None:
        _LOGGER.error("%s - -%s\n" % (self.address_string(), format % args))

    @classmethod
    def route(
        cls,
        url: str,
        methods: list[HttpMethod] = [HttpMethod.GET],
        default_params: dict[str, Any] = {},
    ) -> "function":
        """
        Classmethod to route an url to a function.\n
        All functions should follow this implementation kwargs only:\n


        @RestWebserver.route("url", [HttpMethod.GET])\n
        def get_url(**kwargs):\n
        or if this GET request accepts parameters\n
        def get_url(*, param1 = [], param2 ) [], **kwargs):\n


        @RestWebserver.route("url", [HttpMethod.POST])\n
        def post_url(*, param1, param2, **kwargs):\n

        @RestWebserver.route("url", [HttpMethod.GET, HttpMethod.POST])\n
        def get_post_url(*,HttpMethod_type: HttpMethod, param1=[], param2=[], **kwargs):\n


        If some parameters are missing raise TypeError with a meaningful error description
        """

        def decorator(func):
            return Router().add_route(url, func, methods, default_params)

        return decorator

    def __send_headers(self, http_code: HTTPStatus = HTTPStatus.OK):
        self.send_response(http_code.value)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Methods", "POST, GET")
        self.end_headers()

    def __send_json_response(
        self, response: dict, http_code: HTTPStatus = HTTPStatus.OK
    ):
        self.__send_headers(http_code)
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode())

    def __send_favicon(self):
        self.send_response(200)
        self.send_header("Content-type", "image/x-icon")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(_FAVICO_CONTENT)

    def do_GET(self):
        url = self.path
        if url == "/favicon.ico":
            return self.__send_favicon()
        parsed_url = urlparse(url)
        url = parsed_url.path
        get_params = parse_qs(parsed_url.query)
        get_params["HttpMethod_type"] = HttpMethod.GET
        try:
            handler, params = Router().get_handler(url, HttpMethod.GET)
        except RouteNotFoundError:
            return self.__default_func(**get_params)

        try:
            params = {**get_params, **params}
            self.__send_json_response(handler(**params))
        except TypeError as e:
            self.__send_json_response({"error": str(e)}, HTTPStatus.BAD_REQUEST)

    def do_POST(self):
        url = self.path
        body_post = self.rfile.read(int(self.headers["Content-Length"])).decode()

        # we expect json
        if len(body_post) > 0 and self.headers["Content-Type"] == "application/json":
            try:
                post_params = json.loads(body_post)
            except:
                _LOGGER.exception("can't decode body!")
                post_params = {}
        else:
            _LOGGER.error("not application/json")
            post_params = {}
        post_params["HttpMethod_type"] = HttpMethod.POST
        try:
            handler, params = Router().get_handler(url, HttpMethod.POST)
        except RouteNotFoundError:
            return self.__default_func(**post_params)

        try:
            params = {**post_params, **params}
            self.__send_json_response(handler(**params))
        except TypeError as e:
            self.__send_json_response({"error": str(e)}, HTTPStatus.BAD_REQUEST)
