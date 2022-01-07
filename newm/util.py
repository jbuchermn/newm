import time
import logging
from typing import Any

logger = logging.getLogger(__name__)

def timed(func):  # type: ignore
    def wrapped(*args, **kwargs):  # type: ignore
        t = time.time()
        res = func(*args, **kwargs)
        logger.debug("TIMER[%-30s]  : %7.2fms" % (func.__name__, (time.time() - t) * 1000))
        return res
    return wrapped

def errorlogged(func):  # type: ignore
    def wrapped(*args, **kwargs):  # type: ignore
        try:
            return func(*args, **kwargs)
        except Exception:
            logger.exception("errorlogged")
    return wrapped

def get_color(inp: Any) -> tuple[float, float, float, float]:
    try:
        if isinstance(inp, str):
            r = inp[1:3]
            g = inp[3:5]
            b = inp[5:7]
            if len(inp) >= 9:
                a = inp[7:9]
            else:
                a = "FF"
            return (int(r, 16)/255., int(g, 16)/255., int(b, 16)/255., int(a, 16)/255.)
        elif len(inp) in [3, 4]:
            rf = float(inp[0])
            gf = float(inp[1])
            bf = float(inp[2])
            if len(inp) > 3:
                af = float(inp[3])
            else:
                af = float(inp[3])
            return (min(rf, 1.), min(gf, 1.), min(bf, 1.), min(af, 1.))
        else:
            raise Exception("Unknown")
    except Exception:
        logger.warn("Could not parse color '%s'" % inp)
        return (1., 1., 1., 1.)
