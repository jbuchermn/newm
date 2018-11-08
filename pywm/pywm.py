import sys
import os
import time
import traceback

from .pywm_view import PyWMView

sys.path.append(os.path.join(__file__, ".."))
from build._pywm import (
    run,
    terminate,
    register,
)


_instance = None


def callback(func):
    def wrapped_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            traceback.print_exc()
    return wrapped_func


class PyWM:
    def __init__(self, view_class=PyWMView):
        global _instance
        if _instance is not None:
            raise Exception("Can only have one instance!")
        _instance = self

        register("layout_change", self._layout_change)
        register("motion", self._motion)
        register("motion_absolute", self._motion_absolute)
        register("button", self._button)
        register("axis", self._axis)
        register("key", self._key)
        register("modifiers", self._modifiers)
        register("init_view", self._init_view)
        register("destroy_view", self._destroy_view)

        self._view_class = view_class

        """
        Consider these read-only
        """
        self.views = []
        self.width = 0
        self.height = 0

    @callback
    def _motion(self, time_msec, delta_x, delta_y):
        return self.on_motion(time_msec, delta_x, delta_y)

    @callback
    def _motion_absolute(self, time_msec, x, y):
        return self.on_motion_absolute(time_msec, x, y)

    @callback
    def _button(self, time_msec, button, state):
        return self.on_button(time_msec, button, state)

    @callback
    def _axis(self, time_msec, source, orientation, delta, delta_discrete):
        return self.on_axis(time_msec, source, orientation, delta,
                            delta_discrete)

    @callback
    def _key(self, time_msec, keycode, state):
        return self.on_key(time_msec, keycode, state)

    @callback
    def _modifiers(self, depressed, latched, locked, group):
        return False

    @callback
    def _layout_change(self, width, height):
        self.width = width
        self.height = height
        self.on_layout_change()

    @callback
    def _init_view(self, handle):
        view = self._view_class(self, handle)
        self.views += [view]

    @callback
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

    """
    Virtual methods
    """

    def on_layout_change(self):
        pass

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_motion_absolute(self, time_msec, x, y):
        return False

    def on_button(self, time_msec, button, state):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

    def on_key(self, time_msec, keycode, state):
        return False

    def on_modifiers(self, depressed, latched, locked, group):
        return False
