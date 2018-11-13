import traceback
import time
from threading import Thread

from .pywm_view import PyWMView

from ._pywm import (  # noqa E402
    run,
    terminate,
    register,
)


_instance = None

PYWM_MOD_SHIFT = 1
PYWM_MOD_CAPS = 2
PYWM_MOD_CTRL = 4
PYWM_MOD_ALT = 8
PYWM_MOD_MOD2 = 16
PYWM_MOD_MOD3 = 32
PYWM_MOD_LOGO = 64
PYWM_MOD_MOD5 = 128

PYWM_RELEASED = 0
PYWM_PRESSED = 1


def callback(func):
    def wrapped_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            traceback.print_exc()
    return wrapped_func


class PyWM:
    def __init__(self, view_class=PyWMView, main=None):
        global _instance
        if _instance is not None:
            raise Exception("Can only have one instance!")
        _instance = self

        register("ready", self._ready)
        register("layout_change", self._layout_change)
        register("motion", self._motion)
        register("motion_absolute", self._motion_absolute)
        register("button", self._button)
        register("axis", self._axis)
        register("key", self._key)
        register("modifiers", self._modifiers)
        register("init_view", self._init_view)
        register("destroy_view", self._destroy_view)

        self._main = main
        self._view_class = view_class

        """
        Consider these read-only
        """
        self.views = []
        self.widgets = []
        self.width = 0
        self.height = 0
        self.modifiers = 0

    def _exec_main(self):
        """
        Without XWayland we should wait a little bit
        """
        time.sleep(.1)

        if self._main is not None:
            self._main(self)

    @callback
    def _ready(self):
        Thread(target=self._exec_main).start()

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
    def _key(self, time_msec, keycode, state, keysyms):
        return self.on_key(time_msec, keycode, state, keysyms)

    @callback
    def _modifiers(self, depressed, latched, locked, group):
        self.modifiers = depressed
        return self.on_modifiers(self.modifiers)

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

    def on_widget_destroy(self, widget):
        self.widgets = [v for v in self.widgets if id(v) != id(widget)]

    """
    Public API
    """

    def run(self):
        run()

    def terminate(self):
        terminate()

    def create_widget(self, widget_class, *args, **kwargs):
        widget = widget_class(self, *args, **kwargs)
        self.widgets += [widget]
        return widget

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

    def on_key(self, time_msec, keycode, state, keysyms):
        """
        keycode: raw xkb keycode, probably useless
        state: PYWM_PRESSED, PYWM_RELEASED
        keysyms: translated keysymbols, like "a", "b", "A", "Left", ...
        """
        return False

    def on_modifiers(self, modifiers):
        return False

