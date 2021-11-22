import time
import logging

logger = logging.getLogger(__name__)

def timed_function(func):  # type: ignore
    def wrapped(*args, **kwargs):  # type: ignore
        t = time.time()
        res = func(*args, **kwargs)
        logger.debug("TIMER[%-30s]  : %7.2fms" % (func.__name__, (time.time() - t) * 1000))
        return res
    return wrapped
