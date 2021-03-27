from .lock import lock

def panel(p):
    if p == "lock":
        lock()
    else:
        raise Exception("Unknown panel %s" % p)
