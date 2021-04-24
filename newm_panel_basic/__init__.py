from .lock import lock
from .launcher import launcher

def panel(p: str) -> None:
    if p == "lock":
        lock()
    elif p == "launcher":
        launcher()
    else:
        raise Exception("Unknown panel %s" % p)
