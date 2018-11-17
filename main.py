import sys
import traceback
import faulthandler

from wm import Layout

from pywm import (
    PYWM_MOD_LOGO,
    PYWM_MOD_ALT
)

OUTPUT_SCALE = 2.

mod = PYWM_MOD_LOGO
if len(sys.argv) > 1:
    print("Using modifier ALT")
    mod = PYWM_MOD_ALT
else:
    print("Using modifier LOGO")

faulthandler.enable()
wm = Layout(mod, output_scale=OUTPUT_SCALE, multitouch='/dev/input/event19')
try:
    wm.run()
except Exception:
    traceback.print_exc()
finally:
    wm.terminate()
