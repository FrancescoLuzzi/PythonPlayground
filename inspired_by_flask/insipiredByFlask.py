import logging
from typing import Any

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s %(module)s [%(funcName)s -> %(lineno)d]: %(message)s",
    handlers=[stream_handler],
)
from http.server import HTTPServer
from os.path import dirname, join

from dotenv import load_dotenv
from os import environ

# set FAVICO_PATH env path so that we can find and load the file content
environ["FAVICO_PATH"] = join(dirname(__file__), "favicon.ico")
from rest_server import HttpMethod, RouteWebserver, BadRequestException

_LOGGER = logging.getLogger("inspired_by_flask")

DOTENV_PATH = join(dirname(__file__), ".env")
load_dotenv(DOTENV_PATH)
PORT = int(environ.get("APP_PORT", 8000))


WebApp = HTTPServer(("0.0.0.0", PORT), RouteWebserver)


@RouteWebserver.route("/", [HttpMethod.GET])
def get_ollare(**kwargs):
    return {"response": "GET / HelloWorld!"}


@RouteWebserver.get("/foo")
def get_ollare(*, foo=[], **kwargs):
    return {"response": "GET /foo HelloWorld!", "foo": foo}


@RouteWebserver.post("/foo")
def post_ollare(*, name, surname, **kwargs):
    _LOGGER.info("POST")
    return {"response": "POST /foo HelloWorld!", "name": name, "surname": surname}


@RouteWebserver.route("/bar", [HttpMethod.GET, HttpMethod.POST])
def get_post_swag_stuff(*, HttpMethod_type: "HttpMethod", foo=[], bar=[], **kwargs):
    if not (bar and foo):
        raise BadRequestException("missing parameters foo or bar!")
    return {
        "response": "{} /bar HelloWorld!".format(HttpMethod_type),
        "HttpMethod_type": HttpMethod_type,
        "foo": foo,
        "bar": bar,
    }


@RouteWebserver.route("/multi_params/<first>", default_params={"second": 57})
@RouteWebserver.route("/multi_params/<first>/<int:second>")
def get_multi_params(*, HttpMethod_type: "HttpMethod", first, second):
    return {
        "reponse": "GET /multi_params/<first>/<int:second> HelloWorld!",
        "HttpMethod_type": HttpMethod_type,
        "first": first,
        "second": second,
    }


class Foo:
    __my_id = 0  # type: int

    def __init__(self, id: Any) -> None:
        self.__my_id = id
        RouteWebserver.route_method(
            self.get_simple_response, "/class/{}/function/<bar>".format(self.__my_id)
        )
        RouteWebserver.route_method(
            self.post_simple_response,
            "/class/{}/function".format(self.__my_id),
            [HttpMethod.POST],
        )
        temp_route = RouteWebserver.route_method(
            self.get_multi_response,
            "/class/{}/multi_params/<first>/<int:second>".format(self.__my_id),
            [HttpMethod.GET],
        )
        RouteWebserver.route_method(
            temp_route,
            "/class/{}/multi_params/<first>".format(self.__my_id),
            [HttpMethod.GET],
            {"second": 42},
        )

    def get_simple_response(self, *, HttpMethod_type: "HttpMethod", bar: str):
        return {
            "HttpMethod_type": HttpMethod_type,
            "message": "function called in class, look!! self.__my_id={}".format(
                self.__my_id
            ),
            "bar": bar,
        }

    def post_simple_response(self, *, HttpMethod_type: "HttpMethod", message: str):
        return {
            "HttpMethod_type": HttpMethod_type,
            "message": "function called in class, look!! self.__my_id={}".format(
                self.__my_id
            ),
            "message_received": message,
        }

    def get_multi_response(
        self, *, HttpMethod_type: "HttpMethod", first: str, second: int
    ):
        return {
            "HttpMethod_type": HttpMethod_type,
            "message": "function called in class, look!! self.__my_id={}".format(
                self.__my_id
            ),
            "first": first,
            "second": second,
        }


ollare = Foo(558)


_LOGGER.info("Serving server on http://localhost:{}".format(PORT))
WebApp.serve_forever()
