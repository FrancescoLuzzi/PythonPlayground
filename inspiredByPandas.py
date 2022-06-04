from copy import copy
import random
from time import time_ns
import itertools

counter = itertools.count()


class Element:
    id: int
    number: int
    message: str

    def __init__(self, number: int, message: str) -> None:
        self.id = next(counter)
        self.number = number
        self.message = message


class SmartElement(Element):
    def __eq__(self, __o: Element | int) -> bool:
        if type(__o) == int:
            return self.number == __o
        return self.id == __o.number

    def __ne__(self, __o: Element | int) -> bool:
        return not self.__eq__(__o)

    def __gt__(self, __o: Element | int) -> bool:
        if type(__o) == int:
            return self.number > __o
        return self.number > __o.number

    def __lt__(self, __o: Element | int) -> bool:
        if type(__o) == int:
            return self.number < __o
        return self.number < __o.number

    def __ge__(self, __o: Element | int) -> bool:
        if type(__o) == int:
            return self.number >= __o
        return self.number >= __o.number

    def __le__(self, __o: Element | int) -> bool:
        if type(__o) == int:
            return self.number <= __o
        return self.number <= __o.number

    def __mod__(self, __o: Element | int) -> int:
        if type(__o) == int:
            return self.number % __o
        return self.number % __o.number

    def __repr__(self) -> str:
        return f"{self.message} -> {self.number}"


class IdSeries(tuple):
    def __contains__(self, key) -> bool:
        key_type = type(key)
        if key_type == int:
            return super().__contains__(key)
        elif issubclass(key.__class__, Element):
            return super().__contains__(key.id)
        else:
            raise ValueError(f"Not yet implemented for {key_type.__name__}")


class ElementList:
    elements: list[SmartElement] = []

    def __init__(self, list: list[SmartElement]) -> None:
        self.elements = list


class SmartElementList(ElementList):
    def __contains__(self, key):
        key_type = type(key)
        if key_type == SmartElement:
            for el in self.elements:
                if el.id == key.id:
                    return True
            return False
        else:
            raise ValueError(f"Not yet implemented for {key_type.__name__}")

    def __getitem__(self, key):
        key_type = type(key)
        if key_type == int:
            return self.__class__([self.elements[key]])
        elif key_type == slice:
            return self.__class__(self.elements[key])
        elif key_type == IdSeries:
            return self.__class__([el for el in self.elements if el in key])
        elif issubclass(key.__class__, ElementList):
            return self.__class__([el for el in self.elements if el in key])
        else:
            print(f"No implementation for type {key_type}")

    def __eq__(self, __o: int) -> "IdSeries":
        return IdSeries(el.id for el in self.elements if el == __o)

    def __ne__(self, __o: int) -> "IdSeries":
        return IdSeries(el.id for el in self.elements if el != __o)

    def __gt__(self, __o: int) -> "IdSeries":
        return IdSeries(el.id for el in self.elements if el > __o)

    def __lt__(self, __o: int) -> "IdSeries":
        return IdSeries(el.id for el in self.elements if el < __o)

    def __ge__(self, __o: int) -> "IdSeries":
        return IdSeries(el.id for el in self.elements if el >= __o)

    def __le__(self, __o: int) -> "IdSeries":
        return IdSeries(el.id for el in self.elements if el <= __o)

    def eq(self, __o: int | Element) -> "SmartElementList":
        return self.__class__([el for el in self.elements if el == __o])

    def ne(self, __o: int | Element) -> "SmartElementList":
        return self.__class__([el for el in self.elements if el != __o])

    def gt(self, __o: int | Element) -> "SmartElementList":
        return self.__class__([el for el in self.elements if el > __o])

    def lt(self, __o: int | Element) -> "SmartElementList":
        return self.__class__([el for el in self.elements if el < __o])

    def ge(self, __o: int | Element) -> "SmartElementList":
        return self.__class__([el for el in self.elements if el >= __o])

    def le(self, __o: int | Element):
        return self.__class__([el for el in self.elements if el <= __o])

    def copy(self):
        return self.__class__([copy(el) for el in self.elements])

    def __mod__(self, __o: int):
        out = []
        for el in self.copy().elements:
            el.number = el % __o
            out.append(el)
        return self.__class__(out)

    def __repr__(self) -> str:
        return f"{self.elements}"

    def scramble(self):
        random.seed(time_ns())
        random.shuffle(self.elements)

    def sort(self, reverse: bool = False):
        self.elements.sort(reverse=reverse)


element_list = [
    SmartElement(1, "Hey"),
    SmartElement(2, "Hey"),
    SmartElement(3, "You"),
    SmartElement(4, "Hello"),
    SmartElement(5, "Rock"),
    SmartElement(6, "World"),
]

elements = SmartElementList(element_list)

print(elements[elements % 2 == 1])
print(elements[elements == 1])
