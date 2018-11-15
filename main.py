import traceback
import faulthandler

from wm import Layout

OUTPUT_SCALE = 2.

faulthandler.enable()
wm = Layout(output_scale=OUTPUT_SCALE)
try:
    wm.run()
except Exception:
    traceback.print_exc()
finally:
    wm.terminate()
