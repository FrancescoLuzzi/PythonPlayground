import logging

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

# environ["FAVICO_PATH"] = join(dirname(__file__), "favicon.ico")
from rest_server import HttpMethod, RestWebserver

_LOGGER = logging.getLogger("inspired_by_flask")

DOTENV_PATH = join(dirname(__file__), ".env")
load_dotenv(DOTENV_PATH)
PORT = int(environ.get("APP_PORT", 8000))


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


class Foo:
    self_param: str = "Bar"
    __my_id: int = 0

    def __init__(self, id: int) -> None:
        self.__my_id = id
        RestWebserver.route_method(
            self.get_simple_response, f"/class/{self.__my_id}/function/<bar>"
        )
        RestWebserver.route_method(
            self.post_simple_response,
            f"/class/{self.__my_id}/function",
            [HttpMethod.POST],
        )
        temp_route = RestWebserver.route_method(
            self.get_multi_response,
            f"/class/{self.__my_id}/multi_params/<first>/<int:second>",
            [HttpMethod.GET],
        )
        RestWebserver.route_method(
            temp_route,
            f"/class/{self.__my_id}/multi_params/<first>",
            [HttpMethod.GET],
            {"second": 42},
        )

    def get_simple_response(self, *, HttpMethod_type: HttpMethod, bar: str):
        return {
            "HttpMethod_type": str(HttpMethod_type),
            "message": f"function called in class, look!! {self.self_param=}",
            "bar": bar,
        }

    def post_simple_response(self, *, HttpMethod_type: HttpMethod, message: str):
        return {
            "HttpMethod_type": str(HttpMethod_type),
            "message": f"function called in class, look!! {self.self_param=}",
            "message_received": message,
        }

    def get_multi_response(
        self, *, HttpMethod_type: HttpMethod, first: str, second: int
    ):
        return {
            "HttpMethod_type": str(HttpMethod_type),
            "message": f"function called in class, look!! {self.self_param=}",
            "first": first,
            "second": second,
        }


ollare = Foo(558)


_LOGGER.info(f"Serving server on http://localhost:{PORT}")
WebApp.serve_forever()
