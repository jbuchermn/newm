import logging

from .layout import Layout

from pywm import (
    PYWM_MOD_LOGO,
    # PYWM_MOD_ALT
)

logger = logging.getLogger(__name__)

def run():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(filename)s:%(lineno)s %(asctime)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    for l in ["newm", "pywm"]:
        log = logging.getLogger(l)
        log.setLevel(logging.DEBUG)
        log.addHandler(handler)

    wm = Layout()

    try:
        wm.run()
    except Exception:
        logger.exception("Unexpected")
    finally:
        wm.terminate()
