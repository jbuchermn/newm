import time
import math
from threading import Thread
from pywm import PyWM, PyWMView

class MyView(PyWMView, Thread):
    def __init__(self, handle):
        PyWMView.__init__(self, handle)
        Thread.__init__(self)
        self.set_dimensions(400, 400)
        self.set_box(400, 10, 400, 400)
        self.start()

    def run(self):
        while True:
            time.sleep(0.025)
            self.set_box(400 + 100*math.sin(3*time.time()), 10, 200 + 300*abs(math.cos(time.time())), 400)
            # self.set_dimensions(200 + 300*abs(math.cos(time.time())), 400)

p = PyWM(view_class=MyView)

print("Running...")
p.run()
print("...done")

try:
    while True:
        time.sleep(1)
finally:
    print("Terminating...")
    p.terminate()
    print("...done")
