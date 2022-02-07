from __future__ import annotations
from typing import Optional
import time
import logging
from typing import Any

logger = logging.getLogger(__name__)

class Profile:
    def __init__(self, name: str) -> None:
        self.name = name
        self._cur: Optional[float] = None
        self.ts: list[float] = []
        self.t0 = time.time()

    def start(self) -> None:
        self._cur = time.time()

    def stop(self) -> None:
        if self._cur is None:
            return
        t = time.time()
        self.ts += [t - self._cur]
        self._cur = None

        if t - self.t0 > 1.:
            self.t0 = t
            if len(self.ts) > 0:
                avg = 1000. * sum(self.ts) / len(self.ts)
                ma = 1000. * max(self.ts)
                mi = 1000. * min(self.ts)
                self.ts = []
                logger.debug("TIMER[%-50s]: %7.2fms -- avg %7.2fms -- %7.2fms" % (self.name, mi, avg, ma))


class Profiler:
    def __init__(self) -> None:
        self._profiles: dict[str, Profile] = {}

    def get(self, name: str) -> Profile:
        if name not in self._profiles:
            self._profiles[name] = Profile(name)
        return self._profiles[name]

profiler = Profiler()

def timed(func):  # type: ignore
    profile = profiler.get(str(func))
    def wrapped(*args, **kwargs):  # type: ignore
        profile.start()
        res = func(*args, **kwargs)
        profile.stop()
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
