import sys
import os
import time

sys.path.append(os.path.join(__file__, ".."))
from build._pywm import (
    run,
    terminate,
    register,
    view_get_box,
    view_get_dimensions,
    view_get_title_app_id,
    view_set_box,
    view_set_dimensions
)


_instance = None

class PyWMView:
    def __init__(self, wm, handle):
        self._handle = handle
        self.wm = wm
        self.box = view_get_box(self._handle)

    def set_box(self, x, y, w, h):
        view_set_box(self._handle, x, y, w, h)
        self.box = (x, y, w, h)

    def get_dimensions(self):
        return view_get_dimensions(self._handle)

    def set_dimensions(self, width, height):
        view_set_dimensions(self._handle, round(width), round(height))

    def destroy(self):
        pass

class PyWM:
    def __init__(self, view_class=PyWMView):
        global _instance
        if _instance is not None:
            raise Exception("Can only have one instance!")
        _instance = self

        register("layout_change", self._layout_change)
        register("motion", self._motion)
        register("motion_absolute", self._motion)
        register("button", self._button)
        register("axis", self._axis)
        register("key", self._key)
        register("modifiers", self._modifiers)
        register("init_view", self._init_view)
        register("destroy_view", self._destroy_view)

        self._view_class = view_class
        self.views = []
        self.width = 0
        self.height = 0

    def _layout_change(self, width, height):
        self.width = width
        self.height = height
        print(width, height)

    def _motion(self, *args):
        return False

    def _motion_absolute(self, *args):
        return False

    def _button(self, *args):
        return False

    def _axis(self, *args):
        return False

    def _key(self, *args):
        return False

    def _modifiers(self, *args):
        return False

    def _init_view(self, handle):
        try:
            view = self._view_class(self, handle)
            self.views += [view];
        except Exception as ex:
            print(ex)

    def _destroy_view(self, handle):
        for view in self.views:
            if view._handle == handle:
                view.destroy()
        self.views = [v for v in self.views if v._handle != handle]

    """
    Public API
    """
    
    def run(self):
        run()

    def terminate(self):
        return terminate()

    def init_view(self, view):
        pass

