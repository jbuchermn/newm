import sys
import os

sys.path.append(os.path.join(__file__, ".."))
from build._pywm import (run, terminate, register, view_set_box, view_set_dimensions)


_instance = None

class PyWM:
    def __init__(self):
        global _instance
        if _instance is not None:
            raise Exception("Can only have one instance!")
        _instance = self

        register("motion", self._motion)
        register("motion_absolute", self._motion)
        register("button", self._button)
        register("axis", self._axis)
        register("key", self._key)
        register("modifiers", self._modifiers)
        register("init_view", self._init_view)
        register("destroy_view", self._destroy_view)

    
    def run(self):
        return run()

    def terminate(self):
        return terminate()

    def _motion(self, *args):
        print("motion")
        return False

    def _motion_absolute(self, *args):
        print("motion_absolute")
        return False

    def _button(self, *args):
        print("button")
        return False

    def _axis(self, *args):
        print("axis")
        return False

    def _key(self, *args):
        print("key")
        return False

    def _modifiers(self, *args):
        print("modifiers")
        return False

    def _init_view(self, handle):
        print("init_view", handle)
        view_set_box(handle, 100., 100., 400., 400.);
        view_set_dimensions(handle, 400, 400);
        return False

    def _destroy_view(self, handle):
        print("destroy_view", handle)
        return False
