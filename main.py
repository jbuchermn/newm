import sys
import traceback

from wm import Layout

from pywm import (
    PYWM_MOD_LOGO,
    PYWM_MOD_ALT
)

OUTPUT_SCALE = 2.0

mod = PYWM_MOD_LOGO
if len(sys.argv) > 1 and sys.argv[1] == "ALT":
    print("Using modifier ALT")
    mod = PYWM_MOD_ALT
else:
    print("Using modifier LOGO")

wm = Layout(mod, output_scale=OUTPUT_SCALE, touchpad_device_name="bcm5974", encourage_csd=True)
try:
    wm.run()
except Exception:
    traceback.print_exc()
finally:
    wm.terminate()
