import time
import math
from threading import Thread
from pywm import PyWM, PyWMView

class Anim(Thread):
    def __init__(self, view):
        super().__init__()
        self._view = view
        self._start = time.time() + 10.
        self.start()

    def run(self):
        while time.time() -  self._start < .25:
            dt = time.time() - self._start
            if dt > 0:
                self._view.set_box(0, 0, (1. - 2.*dt) * self._view.wm.width, (1. - 2.*dt) * self._view.wm.height)
            time.sleep(0.02)

        self._view.set_dimensions(.5 * self._view.wm.width, .5 * self._view.wm.height)


class MyView(PyWMView):
    def __init__(self, wm, handle):
        super().__init__(wm, handle)
        self.set_dimensions(wm.width, wm.height)
        self.set_box(0, 0, wm.width, wm.height)
        Anim(self)


p = PyWM(view_class=MyView)

print("Running...")
p.run()

try:
    while True:
        time.sleep(1)
finally:
    print("Terminating...")
    p.terminate()
