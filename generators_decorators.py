import collections
from typing import Callable
from functools import wraps
# source https://www.youtube.com/watch?v=tmeKsb2Fras

def logger(f:Callable):
    @wraps(f)
    def decorator(*args,**kwargs):
        try:
            print(f"setup {f.__name__}")
            yield from f(*args,**kwargs)
        finally:
            print(f"cleanup {f.__name__}")
    return decorator


@logger
def worker(f:Callable):
    tasks = collections.deque()
    value = None
    while True:
        batch = yield value
        value = None
        if batch is not None:
            tasks.extend(batch)
        else:
            if tasks:
                args = tasks.popleft()
                value = f(*args)


def quiet_worker(f):
    while True:
        w = worker(f)
        try:
            yield from w
        except Exception as exc:
            print(f"ignoring {exc.__class__.__name__}")

def example_worker():
    w = worker(str)
    print(worker.__name__)
    w.send(None)
    w.send([("starting up",), (1,), (2,), (3,)])
    print(next(w))
    print(next(w))
    print(next(w))
    print(next(w))

    w.send([(4,), (5,)])
    print(next(w))
    print(next(w))

    w.send([(7,), (8,)])
    print(next(w))
    print(next(w))

    w.close()

example_worker()