import sys
from sys import argv
from time import sleep
import random

n = 0
tot = 70


def notify(num, found):
    if found.get(num, None):
        times = round(tot * num / n)
        time = tot - times
        sleep(random.random() * 0.1)
        if num == n - 2:
            print("|" + "=" * int(tot) + ">" + "|")
            sys.stdout.flush()
            sleep(0.5)
        else:
            print("|" + "=" * times + ">" + " " * (time) + "|", end="\r")


def fibo(num: int, found: dict):
    notify(num=num, found=found)
    if num == 2 or num == 1:
        return 1
    elif found.get(num) != None:
        return found.get(num)
    else:
        g = fibo(num - 1, found) + fibo(num - 2, found)
        found[num] = g
        return g


if argv.__len__() == 1:
    i = input("Enter a number: ")
else:
    i = argv[1]
if i != "":
    try:
        n = int(i)
        fib = fibo(num=n, found={})
        print(f"End calculation...\nFibo({n})={fib}")
        print(f"Number of digits:{str(fib).__len__()}")
    except Exception as E:
        print("parsing error")
        print(E)
else:
    print("input error")
