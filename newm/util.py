import time
import sys

def timed_function(func):  # type: ignore
    def wrapped(*args, **kwargs):  # type: ignore
        t = time.time()
        res = func(*args, **kwargs)
        print("TIMER[%-30s]  : %fms" % (func.__name__, (time.time() - t) * 1000), file=sys.stderr)
        return res
    return wrapped
