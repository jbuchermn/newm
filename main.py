import time
from pywm import PyWM

p = PyWM()

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
