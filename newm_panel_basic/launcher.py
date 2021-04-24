import os
import time

def launcher() -> None:
    while True:
        os.system("clear")
        prog = input("Launch?")
        os.system("newm-cmd launcher %s" % prog)
