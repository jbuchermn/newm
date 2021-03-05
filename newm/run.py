import sys
import logging

from .layout import Layout

from pywm import (
    PYWM_MOD_LOGO,
    # PYWM_MOD_ALT
)

def run():
    logging.basicConfig(format='[%(levelname)s] %(filename)s:%(lineno)s %(asctime)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

    wm = Layout(
        PYWM_MOD_LOGO,
        xkb_model="macintosh",
        xkb_layout="de,de",
        xkb_options="caps:escape",
        output_scale=2.0,

        # See comments in view.py
        xwayland_handle_scale_clientside=True,
        enable_output_manager=False,

        touchpad_device_name="bcm5974",
        wallpaper="/home/jonas/wallpaper.jpg",
        encourage_csd=False,
        panel_dir="/home/jonas/newm/panel"
    )

    try:
        wm.run()
    except Exception:
        logging.exception("Unexpected")
    finally:
        wm.terminate()
