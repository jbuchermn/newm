import sys
import logging

from wm import Layout

from pywm import (
    PYWM_MOD_LOGO,
    PYWM_MOD_ALT
)

logging.basicConfig(format='[%(levelname)s] %(filename)s:%(lineno)s %(asctime)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S.%f', level=logging.DEBUG)

mod = PYWM_MOD_LOGO
if len(sys.argv) > 1 and sys.argv[1] == "ALT":
    logging.info("Using modifier ALT")
    mod = PYWM_MOD_ALT
else:
    logging.info("Using modifier LOGO")


wm = Layout(
    mod,
    xkb_model="macintosh",
    xkb_layout="de,de",
    xkb_options="caps:escape",
    output_scale=2.0,
    touchpad_device_name="bcm5974",
    wallpaper="~/wallpaper.jpg",
    encourage_csd=False)

try:
    wm.run()
except Exception:
    logging.exception("Unexpected")
finally:
    wm.terminate()
