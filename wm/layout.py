import time
import math
import os
from itertools import product
from threading import Thread

from pywm import (
    PyWM,
    PYWM_MOD_CTRL,
    PYWM_PRESSED,
    PYWM_MOD_ALT,
    PYWM_MOD_LOGO
)

from pywm.touchpad import (
    TwoFingerSwipePinchGesture,
    HigherSwipeGesture,
    SingleFingerMoveGesture
)

from .state import LayoutState
from .view import View

from .key_processor import KeyProcessor, KeyBinding
from .panel_endpoint import PanelEndpoint
from .sys_backend import SysBackend

from .widget import (
    TopBar,
    BottomBar,
    Background,
    Corner
)
from .overlay import (
    MoveResizeOverlay,
    SwipeOverlay,
    SwipeToZoomOverlay,
    LauncherOverlay,
    OverviewOverlay
)

# def _box_intersects(box1, box2):
#     box1_tiles = []
#     for i, j in product(range(math.floor(box1[0]),
#                               math.ceil(box1[0] + box1[2])),
#                         range(math.floor(box1[1]),
#                               math.ceil(box1[1] + box1[3]))):
#         box1_tiles += [(i, j)]
#
#     box2_tiles = []
#     for i, j in product(range(math.floor(box2[0]),
#                               math.ceil(box2[0] + box2[2])),
#                         range(math.floor(box2[1]),
#                               math.ceil(box2[1] + box2[3]))):
#         box2_tiles += [(i, j)]
#
#     for t in box1_tiles:
#         if t in box2_tiles:
#             return True
#     return False
#


class Layout(PyWM):
    def __init__(self, mod, **kwargs):
        super().__init__(View, **kwargs)

        self.mod = mod
        self.mod_sym = None
        if mod == PYWM_MOD_ALT:
            self.mod_sym = "Alt"
        elif mod == PYWM_MOD_LOGO:
            self.mod_sym = "Super"
        else:
            raise Exception("Unknown mod")

        self.key_processor = KeyProcessor(self.mod_sym)
        self.key_processor.register_bindings(
            ("M-h", lambda: self.move(-1, 0)),
            ("M-j", lambda: self.move(0, 1)),
            ("M-k", lambda: self.move(0, -1)),
            ("M-l", lambda: self.move(1, 0)),

            ("M-Return", lambda: os.system("termite &")),
            ("M-c", lambda: os.system("chromium --enable-features=UseOzonePlatform --ozone-platform=wayland &")),  # noqa E501
            ("M-q", lambda: self.close_view()),  # noqa E501

            ("M-f", lambda: self.toggle_padding()),

            ("M-C", lambda: self.terminate()),
            ("ModPress", lambda: self.enter_overlay(OverviewOverlay(self))),  # noqa E501

        )

        self.sys_backend = SysBackend(self)
        self.sys_backend.register_xf86_keybindings()

        self.state = None

        self.overlay = None

        self.background = None
        self.top_bar = None
        self.bottom_bar = None
        self.corners = []

        self.panel_endpoint = None

        self.fullscreen_backup = 0, 0, 1

        """
        - next state
        - start time
        - duration
        """
        self._animation = None

    def main(self):

        self.state = LayoutState()

        self.bottom_bar = self.create_widget(BottomBar)
        self.top_bar = self.create_widget(TopBar)
        self.background = self.create_widget(Background,
                                             '~/wallpaper.jpg')
        self.corners = [
            self.create_widget(Corner, True, True),
            self.create_widget(Corner, True, False),
            self.create_widget(Corner, False, True),
            self.create_widget(Corner, False, False)
        ]

        self.panel_endpoint = PanelEndpoint()

    def terminate(self):
        super().terminate()
        if self.top_bar is not None:
            self.top_bar.stop()
        if self.bottom_bar is not None:
            self.bottom_bar.stop()
        if self.panel_endpoint is not None:
            self.panel_endpoint.stop()

    def _execute_view_main(self, view):
        view.main(self.state)

    def damage(self):
        for _, v in self._views.items():
            v.damage()

        if self.background is not None:
            self.background.damage()

        if self.top_bar is not None:
            self.top_bar.damage()

        if self.bottom_bar is not None:
            self.bottom_bar.damage()


    def update(self, new_state):
        self.state = new_state
        self.damage()

    def animate_to(self, new_state, dt, then=None):
        if self._animation is not None:
            return

        if id(new_state) == id(self.state):
            return

        # Prevent devision by zero
        dt = max(dt, 0.1)

        self._animation = (new_state, time.time(), dt)
        for _, v in self._views.items():
            v.animate(self.state, new_state, dt)

        if self.background is not None:
            self.background.animate(self.state, new_state, dt)

        if self.top_bar is not None:
            self.top_bar.animate(self.state, new_state, dt)

        if self.bottom_bar is not None:
            self.bottom_bar.animate(self.state, new_state, dt)

        def run():
            time.sleep(dt)
            self.state = self._animation[0]
            self._animation = None
            if then is not None:
                then()

        Thread(target=run).start()



    """
    Utilities
    """

    def windows(self):
        return [v for _, v in self._views.items() if v.is_window()]

    def dialogs(self): 
        return [v for _, v in self._views.items() if v.is_dialog()]

    def panels(self):
        return [v for _, v in self._views.items() if v.is_panel()]

    def find_focused_box(self):
        for _, view in self._views.items():
            if view.up_state.is_focused:
                view_state = self.state.get_view_state(view._handle)
                return view_state.i, view_state.j, view_state.w, view_state.h

        return 0, 0, 1, 1

    def find_focused_view(self):
        for _, view in self._views.items():
            if view.up_state.is_focused:
                return view

        return None

    def place_initial(self, view, w, h):
        place_i = 0
        place_j = 0
        for j, i in product(range(math.floor(self.state.j),
                                  math.ceil(self.state.j + self.state.size)),
                            range(math.floor(self.state.i),
                                  math.ceil(self.state.i + self.state.size))):
            for jp, ip in product(range(j, j + h), range(i, i + w)):
                if not self.state.is_tile_free(ip, jp):
                    break
            else:
                place_i, place_j = i, j
                break
        else:
            place_i, place_j = self.state.i, self.state.j
            while not self.state.is_tile_free(place_i, place_j):
                place_i += 1

        return place_i, place_j


    """
    Callbacks
    """

    def on_key(self, time_msec, keycode, state, keysyms):
        if self.overlay is not None and self.overlay.ready():
            if self.overlay.on_key(time_msec, keycode, state, keysyms):
                return True

        return self.key_processor.on_key(state == PYWM_PRESSED,
                                         keysyms,
                                         self.modifiers & self.mod > 0,
                                         self.modifiers & PYWM_MOD_CTRL > 0)

    def on_motion(self, time_msec, delta_x, delta_y):
        if self.overlay is not None and self.overlay.ready():
            return self.overlay.on_motion(time_msec, delta_x, delta_y)

        if self.modifiers & self.mod:
            ovr = MoveResizeOverlay(self)
            ovr.on_motion(time_msec, delta_x, delta_y)
            self.enter_overlay(ovr)
            return True

        return False

    def on_button(self, time_msec, button, state):
        if self.overlay is not None and self.overlay.ready():
            return self.overlay.on_button(time_msec, button, state)

        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        if self.overlay is not None and self.overlay.ready():
            return self.overlay.on_axis(time_msec, source, orientation,
                                        delta, delta_discrete)

        return False

    def on_gesture(self, gesture):
        if self.overlay is not None and self.overlay.ready():
            return self.overlay.on_gesture(gesture)
        elif self.overlay is None:
            if self.modifiers & self.mod and \
                    (isinstance(gesture, TwoFingerSwipePinchGesture) or
                     isinstance(gesture, SingleFingerMoveGesture)):
                ovr = MoveResizeOverlay(self)
                ovr.on_gesture(gesture)
                self.enter_overlay(ovr)
                return True

            if isinstance(gesture, HigherSwipeGesture) \
                    and gesture.n_touches == 3:
                ovr = SwipeOverlay(self)
                ovr.on_gesture(gesture)
                self.enter_overlay(ovr)
                return True

            if isinstance(gesture, HigherSwipeGesture) \
                    and gesture.n_touches == 4:
                ovr = SwipeToZoomOverlay(self)
                ovr.on_gesture(gesture)
                self.enter_overlay(ovr)
                return True

            if isinstance(gesture, HigherSwipeGesture) \
                    and gesture.n_touches == 5:
                ovr = LauncherOverlay(self)
                ovr.on_gesture(gesture)
                self.enter_overlay(ovr)
                return True

            return False


    """
    Actions
    """

    def enter_overlay(self, overlay):
        self.key_processor.on_other_action()
        if self.overlay is not None:
            return

        self.overlay = overlay
        self.overlay.init()

    def exit_overlay(self):
        if self.overlay is None:
            return

        self.overlay.destroy()

    def on_overlay_destroyed(self):
        self.overlay = None

    def move(self, delta_i, delta_j):
        i, j, w, h = self.find_focused_box()
        ci, cj = i + w/2., j + h/2.

        if ((i + w > self.state.i + self.state.size and delta_i > 0) or
                (i < self.state.i and delta_i < 0) or
                (j + h > self.state.j + self.state.size and delta_j > 0) or
                (j < self.state.j and delta_j < 0)):

            vf = None
            for _, v in self._views.items():
                if v.up_state.is_focused:
                    vf = v
            if vf is not None:
                self.focus_view(vf)
                return

        def score(view):
            cvi, cvj = view.state.i + view.state.w/2., \
                view.state.j + view.state.h/2.
            sp = (cvi - ci) * delta_i + (cvj - cj) * delta_j
            sp *= ((cvi - ci) ** 2) + ((cvj - cj) ** 2)
            return sp

        best_view = None
        best_view_score = 1000

        for _, view in self._views.items():
            s = score(view)
            if s > 0. and s < best_view_score:
                best_view_score = s
                best_view = view

        if best_view is not None:
            self.focus_view(best_view)


    def close_view(self):
        view = [v for _, v in self._views.items() if v.up_state.is_focused]
        if len(view) == 0:
            return

        view = view[0]
        view.close()


    def focus_view(self, view):
        view.focus()
        self.animate_to(
            self.state.focussing_view(
                view._handle),
            .3
        )


    def toggle_padding(self):
        bu = None
        fb = None

        if self.state.padding > 0:
            for _, v in self._views.items():
                if v.is_window():
                    v.set_fullscreen(True)

            self.fullscreen_backup = self.state.i, self.state.j, \
                self.state.size
            fb = self.find_focused_box()
        else:
            for _, v in self._views.items():
                if v.is_window():
                    v.set_fullscreen(False)

            if self.fullscreen_backup:
                bu = self.fullscreen_backup
                self.fullscreen_backup = None


        self.animate_to(
            self.state.with_padding_toggled(
                reset=bu,
                focus_box=fb
            ), .3)


