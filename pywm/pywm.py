import sys
import os

sys.path.append(os.path.join(__file__, ".."))
from build._pywm import (run, terminate)


_instance = None

class PyWM:
    def __init__(self):
        global _instance
        if _instance is not None:
            raise Exception("Can only have one instance!")
        _instance = self
    
    def run(self):
        return run()

    def terminate(self):
        return terminate()
