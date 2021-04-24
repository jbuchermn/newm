import os
import logging

from .lock import lock
from .launcher import launcher

logger = logging.getLogger(__name__)

def panel(p: str) -> None:
    handler = logging.FileHandler(os.environ['HOME'] + '/.cache/newm_panel_log' if 'HOME' in os.environ else '/tmp/newm_panel_log')
    formatter = logging.Formatter('[%(levelname)s] %(filename)s:%(lineno)s %(asctime)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    """
    Prevent stdout misuse
    """
    logging.getLogger().propagate = False
    logger.propagate = False

    if p == "lock":
        lock()
    elif p == "launcher":
        launcher()
    else:
        raise Exception("Unknown panel %s" % p)
