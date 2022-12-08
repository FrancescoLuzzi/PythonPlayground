import json
import logging
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import environ
from os.path import dirname, join
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from http import HTTPStatus
from router.http_utils import HttpMethod
from router.router import Router, RouteNotFoundError
from typing import Any

from dotenv import load_dotenv


stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s %(module)s [%(funcName)s -> %(lineno)d]: %(message)s",
    handlers=[stream_handler],
)

_LOGGER = logging.getLogger(__name__ if __name__ != "__main__" else Path(__file__).stem)

DOTENV_PATH = join(dirname(__file__), ".env")
load_dotenv(DOTENV_PATH)
PORT = int(environ.get("APP_PORT", 8000))

FAVICO_PATH = join(dirname(__file__), "favicon.ico")

Router()


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
        try:
            with open(FAVICO_PATH, "rb") as favicon_file:
                self.wfile.write(favicon_file.read())
        except FileNotFoundError:
            _LOGGER.warning(f"favico file not found in -> {FAVICO_PATH}")

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


WebApp = HTTPServer(("0.0.0.0", PORT), RestWebserver)


@RestWebserver.route("/", [HttpMethod.GET])
def get_ollare(**kwargs):
    return {"response": "HelloWorld!"}


@RestWebserver.route("/foo", [HttpMethod.GET])
def get_ollare(*, foo=[], **kwargs):
    return {"response": "GET HelloWorld!", "foo": foo}


@RestWebserver.route("/foo", [HttpMethod.POST])
def post_ollare(*, name, surname, **kwargs):
    _LOGGER.info("POST")
    return {"response": "POST HelloWorld!", "name": name, "surname": surname}


@RestWebserver.route("/bar", [HttpMethod.GET, HttpMethod.POST])
def get_post_swag_stuff(*, HttpMethod_type: HttpMethod, foo=[], bar=[], **kwargs):
    return {
        "response": f"{HttpMethod_type} HelloWorld!",
        "HttpMethod_type": str(HttpMethod_type),
        "foo": foo,
        "bar": bar,
    }


@RestWebserver.route("/multi_params/<first>", default_params={"second": 57})
@RestWebserver.route("/multi_params/<first>/<int:second>")
def get_multi_params(*, HttpMethod_type: HttpMethod, first, second):
    return {
        "HttpMethod_type": str(HttpMethod_type),
        "first": first,
        "second": second,
    }


_LOGGER.info(f"Serving server on http://localhost:{PORT}")
WebApp.serve_forever()
