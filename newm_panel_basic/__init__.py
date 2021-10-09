import os
import logging

from .lock import lock
from .launcher import launcher

logger = logging.getLogger(__name__)

def panel(p: str) -> None:
    path = os.environ['HOME'] if 'HOME' in os.environ else '/'
    if path.strip() == '/':
        path = '/tmp'
    else:
        path += '/.cache'

    handler = logging.FileHandler(path + '/newm_panel_log')
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
