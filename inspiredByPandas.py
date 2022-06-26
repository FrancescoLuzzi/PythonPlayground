from copy import copy
import random
from time import time_ns
import itertools

counter = itertools.count()


class Element:
    __id: int
    ordering_value: int
    string_content: str

    def __init__(self, ordering_value: int, string_content: str) -> None:
        self.__id = next(counter)
        self.ordering_value = ordering_value
        self.string_content = string_content

    def get_id(self):
        return self.__id

    def __repr__(self) -> str:
        return f"{self.string_content} -> {self.ordering_value}"


class SmartElement(Element):
    def __eq__(self, __o: Element | int) -> bool:
        if type(__o) == int:
            return self.ordering_value == __o
        return self.ordering_value == __o.ordering_value

    def __ne__(self, __o: Element | int) -> bool:
        return not self.__eq__(__o)

    def __gt__(self, __o: Element | int) -> bool:
        if type(__o) == int:
            return self.ordering_value > __o
        return self.ordering_value > __o.ordering_value

    def __lt__(self, __o: Element | int) -> bool:
        if type(__o) == int:
            return self.ordering_value < __o
        return self.ordering_value < __o.ordering_value

    def __ge__(self, __o: Element | int) -> bool:
        if type(__o) == int:
            return self.ordering_value >= __o
        return self.ordering_value >= __o.ordering_value

    def __le__(self, __o: Element | int) -> bool:
        if type(__o) == int:
            return self.ordering_value <= __o
        return self.ordering_value <= __o.ordering_value

    def __mod__(self, __o: Element | int) -> int:
        if type(__o) == int:
            return self.ordering_value % __o
        return self.ordering_value % __o.ordering_value


class IdSeries(tuple):
    def __contains__(self, key) -> bool:
        key_type = type(key)
        if key_type == int:
            return super().__contains__(key)
        elif issubclass(key.__class__, Element):
            return super().__contains__(key.get_id())
        else:
            raise ValueError(f"Not yet implemented for {key_type.__name__}")


class ElementList:
    elements: list[SmartElement] = []

    def __init__(self, list: list[SmartElement]) -> None:
        self.elements = list


class SmartElementList(ElementList):
    def get_id_series(self):
        return IdSeries(el.get_id() for el in self.elements)

    def __contains__(self, key):
        key_type = type(key)
        if issubclass(key_type, SmartElement):
            for el in self.elements:
                if el.get_id() == key.get_id():
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
            raise ValueError(f"Not yet implemented for {key_type.__name__}")

    def __add__(self, __o: SmartElement):
        key_type = type(__o)
        if issubclass(key_type, SmartElement):
            out = self.copy()
            out.elements.append(__o)
            return out
        else:
            raise ValueError(f"Not yet implemented for {key_type.__name__}")

    def __sub__(self, __o: SmartElement):
        key_type = type(__o)
        if issubclass(key_type, SmartElement):
            out_ids = self.get_id_series()
            indx = out_ids.index(__o.get_id())
            return self[IdSeries(out_ids[:indx] + out_ids[indx + 1 :])]
        else:
            raise ValueError(f"Not yet implemented for {key_type.__name__}")

    def __eq__(self, __o: int) -> "IdSeries":
        return IdSeries(el.get_id() for el in self.elements if el == __o)

    def __ne__(self, __o: int) -> "IdSeries":
        return IdSeries(el.get_id() for el in self.elements if el != __o)

    def __gt__(self, __o: int) -> "IdSeries":
        return IdSeries(el.get_id() for el in self.elements if el > __o)

    def __lt__(self, __o: int) -> "IdSeries":
        return IdSeries(el.get_id() for el in self.elements if el < __o)

    def __ge__(self, __o: int) -> "IdSeries":
        return IdSeries(el.get_id() for el in self.elements if el >= __o)

    def __le__(self, __o: int) -> "IdSeries":
        return IdSeries(el.get_id() for el in self.elements if el <= __o)

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
            el.ordering_value = el % __o
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


def __example():
    elements = SmartElementList(element_list)
    el = SmartElement(9, "Added later")
    els = elements + el
    print(els)
    el2 = SmartElement(9, "Added later 2")
    try:
        els = els - el2
    except ValueError:
        print("Can't do that, those items have different ids!!")
    els -= el
    print(els)
    print(elements[elements % 2 == 1])
    print(elements[elements == 1])


if __name__ == "__main__":
    __example()
