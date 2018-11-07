import sys
import os

sys.path.append(os.path.join(__file__, ".."))
from build._pywm import (run, terminate, register)


_instance = None

class PyWM:
    def __init__(self):
        global _instance
        if _instance is not None:
            raise Exception("Can only have one instance!")
        _instance = self

        register("motion", self.motion)
        register("motion_absolute", self.motion)
        register("button", self.button)
        register("axis", self.axis)
        register("key", self.key)
        register("modifiers", self.modifiers)

    
    def run(self):
        return run()

    def terminate(self):
        return terminate()

    def motion(self, *args):
        print("Motion")
        return False

    def motion_absolute(self, *args):
        print("MotionAbsolute")
        return False

    def button(self, *args):
        print("Button")
        return False

    def axis(self, *args):
        print("Axis")
        return False

    def key(self, *args):
        print("Key")
        return False

    def modifiers(self, *args):
        print("Modifiers")
        return False
