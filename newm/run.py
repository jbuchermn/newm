from __future__ import annotations
from typing import Optional

import logging

from .layout import Layout

logger = logging.getLogger(__name__)

def run(debug: bool=False, config_file: Optional[str]=None) -> None:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(filename)s:%(lineno)s %(asctime)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    handler.setLevel(logging.DEBUG if debug else logging.INFO)
    handler.setFormatter(formatter)

    for l in ["newm", "pywm"]:
        log = logging.getLogger(l)
        log.setLevel(logging.DEBUG)
        log.addHandler(handler)

    wm = Layout(debug=debug, config_file=config_file)

    try:
        wm.run()
    except Exception:
        logger.exception("Unexpected")
    finally:
        wm.terminate()
