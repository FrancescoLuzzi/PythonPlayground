from enum import Enum


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"

    def __str__(self) -> str:
        return self.value
