import sys
import traceback

from wm import Layout

from pywm import (
    PYWM_MOD_LOGO,
    PYWM_MOD_ALT
)

OUTPUT_SCALE = 1.666

mod = PYWM_MOD_LOGO
if len(sys.argv) > 1 and sys.argv[1] == "ALT":
    print("Using modifier ALT")
    mod = PYWM_MOD_ALT
else:
    print("Using modifier LOGO")

wm = Layout(mod, output_scale=OUTPUT_SCALE)
try:
    wm.run()
except Exception:
    traceback.print_exc()
finally:
    wm.terminate()
