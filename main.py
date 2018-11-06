import time
from threading import Thread
from pywm import PyWM

p = PyWM()

print("Running...")
p.run()
print("...done")

time.sleep(10)

print("Terminating...")
p.terminate()
print("...done")
