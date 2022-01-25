from __future__ import annotations
from typing import Optional
import time

import logging
try:
    import yappi
    YAPPI = True
except:
    YAPPI = False

from .layout import Layout

logger = logging.getLogger(__name__)

def run(debug: bool=False, profile: bool=False, config_file: Optional[str]=None) -> None:
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
        if profile and YAPPI:
            yappi.start()
        wm.run()
    except Exception:
        logger.exception("Unexpected")
    finally:
        wm.terminate()

        if profile and YAPPI:
            time.sleep(2.)
            yappi.stop()
            for thread in yappi.get_thread_stats():
                print("----------- THREAD (%s) (%d) ----------------" % (thread.name, thread.id))
                for s in yappi.get_func_stats(ctx_id=thread.id):
                    where = "%s-%s:%d" % (s.module, s.name, s.lineno)
                    if len(where) > 100:
                        where = where[-100:]

                    print("%0100s %5d * %.10f = %.10f (%.10f)" % (where, s.ncall, s.tavg, s.ttot, s.tsub))

