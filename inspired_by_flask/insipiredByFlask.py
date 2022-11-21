import json
import logging
import socketserver
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import environ
from os.path import dirname, join
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv


class WebMethod(Enum):
    GET = "GET"
    POST = "POST"


stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(module)s [%(funcName)s -> %(lineno)d]: %(message)s",
    handlers=[stream_handler],
)

_LOGGER = logging.getLogger(__name__)

DOTENV_PATH = join(dirname(__file__), ".env")
load_dotenv(DOTENV_PATH)
FAVICO_PATH = join(dirname(__file__), "favicon.ico")


class MyWebserver(BaseHTTPRequestHandler):
    routing = {}

    def __init__(
        self,
        request: bytes,
        client_address: tuple[str, int],
        server: socketserver.BaseServer,
    ) -> None:
        super().__init__(request, client_address, server)

    def __default_func(self, *args, **kwargs):
        self.send_response(404)
        self.end_headers()
        _LOGGER.warning(f"{self.path} request not mapped")

    def log_message(self, format: str, *args) -> None:
        _LOGGER.info("%s - - %s\n" % (self.address_string(), format % args))

    def log_error(self, format: str, *args) -> None:
        _LOGGER.error("%s - -%s\n" % (self.address_string(), format % args))

    @classmethod
    def route(cls, url: str, methods: list[WebMethod] = [WebMethod.GET]) -> "function":
        def decorator(func):
            if url not in cls.routing:
                cls.routing[url] = {}

            for method in methods:
                if method not in cls.routing[url]:
                    cls.routing[url][method] = func
            return func

        return decorator

    def __send_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Methods", "POST, GET")
        self.end_headers()

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
        # if url not mapped
        if url not in self.routing:
            return self.__default_func()

        self.__send_json_response(
            self.routing[url].get(WebMethod.GET, self.__default_func)(**get_params)
        )

    def do_POST(self):
        url = self.path
        body_post = self.rfile.read(int(self.headers["Content-Length"])).decode()

        # if url not mapped
        if url not in self.routing:
            return self.__default_func()

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
        self.__send_json_response(
            self.routing[url].get(WebMethod.POST, self.__default_func)(**post_params)
        )

    def __send_json_response(self, response: dict):
        self.__send_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode())


PORT = environ.get("APP_PORT", 8000)

WebApp = HTTPServer(("0.0.0.0", PORT), MyWebserver)


@MyWebserver.route("/ollare", [WebMethod.GET])
def func(ollare=None, **kwargs):
    return {"response": "GET HelloWorld!", "ollare": ollare}


@MyWebserver.route("/ollare", [WebMethod.POST])
def func(name=None, surname=None, **kwargs):
    _LOGGER.info("POST")
    return {"response": "POST HelloWorld!", "name": name, "surname": surname}


WebApp.serve_forever()
