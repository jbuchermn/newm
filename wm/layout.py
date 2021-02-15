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

from .view import View, ViewState

from .bar import TopBar, BottomBar
from .background import Background
from .corner import Corner

from .key_processor import KeyProcessor, KeyBinding
from .panel_endpoint import PanelEndpoint
from .sys_backend import SysBackend

from .move_resize_overlay import MoveResizeOverlay
from .swipe_overlay import SwipeOverlay
from .swipe_to_zoom_overlay import SwipeToZoomOverlay
from .launcher_overlay import LauncherOverlay
from .overview_overlay import OverviewOverlay


class LayoutState:
    def __init__(self, i, j, size, scale, min_i, min_j, max_i, max_j, padding,
                 background_factor, top_bar_dy, bottom_bar_dy):
        self.i = i
        self.j = j
        self.size = size
        self.scale = scale
        self.min_i = min_i
        self.min_j = min_j
        self.max_i = max_i
        self.max_j = max_j
        self.padding = padding
        self.background_factor = background_factor
        self.top_bar_dy = top_bar_dy
        self.bottom_bar_dy = bottom_bar_dy

    def copy(self):
        return LayoutState(
            self.i,
            self.j,
            self.size,
            self.scale,
            self.min_i,
            self.min_j,
            self.max_i,
            self.max_j,
            self.padding,
            self.background_factor,
            self.top_bar_dy,
            self.bottom_bar_dy)

    def __str__(self):
        return str(self.__dict__)


def _box_intersects(box1, box2):
    box1_tiles = []
    for i, j in product(range(math.floor(box1[0]),
                              math.ceil(box1[0] + box1[2])),
                        range(math.floor(box1[1]),
                              math.ceil(box1[1] + box1[3]))):
        box1_tiles += [(i, j)]

    box2_tiles = []
    for i, j in product(range(math.floor(box2[0]),
                              math.ceil(box2[0] + box2[2])),
                        range(math.floor(box2[1]),
                              math.ceil(box2[1] + box2[3]))):
        box2_tiles += [(i, j)]

    for t in box1_tiles:
        if t in box2_tiles:
            return True
    return False



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

            # ("M-s", lambda: self.toggle_half_scale()),
            ("M-f", lambda: self.toggle_padding()),

            ("M-C", lambda: self.terminate()),
            ("ModPress", lambda: self.enter_overlay(OverviewOverlay(self))),  # noqa E501

        )

        self.sys_backend = SysBackend(self)
        self.sys_backend.register_xf86_keybindings()

        self.default_padding = 0.01
        self.state = None

        self.overlay = None

        self.background = None
        self.top_bar = None
        self.bottom_bar = None
        self.corners = []

        self.panel_endpoint = None

        """
        scale == size: pixel-to-pixel
        scale == 2 * size: client-side width height are twice as
            high as rendered width, height => Appears half as big
        ...
        """
        self.is_half_scale = False

        self.fullscreen_backup = 0, 0, 1

        """
        - next state
        - start time
        - duration
        """
        self._animation = None

    def main(self):

        self.state = LayoutState(0, 0, 2, 2, 0, 0, 1, 1,
                                 self.default_padding, 3, 0, 0)
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


    def damage(self):
        for _, v in self._views.items():
            if isinstance(v.state, ViewState):
                v.state.parent = self.state
            v.damage()

        if self.background is not None:
            self.background.damage()

        if self.top_bar is not None:
            self.top_bar.damage()

        if self.bottom_bar is not None:
            self.bottom_bar.damage()


    def animate_to(self, new_state, then=None):
        if self._animation is not None:
            return

        print("Animating to %s" % new_state.__dict__)

        self._animation = (new_state, time.time(), .3)
        for _, v in self._views.items():
            if v.is_window() or v.is_dialog():
                state = v.state.copy()
                state.parent = new_state
                v.animate_to(state)

        if self.background is not None:
            self.background.animate_to(new_state)

        if self.top_bar is not None:
            self.top_bar.animate_to(new_state)

        if self.bottom_bar is not None:
            self.bottom_bar.animate_to(new_state)

        def run():
            time.sleep(self._animation[1] + self._animation[2] - time.time())
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

    def find_at_tile(self, i, j):
        for view in self.windows():
            if view.state is None:
                continue
            if (round(view.state.i) <= round(i) < round(view.state.i + view.state.w)) and \
                    (round(view.state.j) <= round(j) < round(view.state.j + view.state.h)):
                return view

        return None

    def find_focused_box(self):
        for _, view in self._views.items():
            if view.up_state.is_focused:
                return view.state.i, view.state.j, view.state.w, view.state.h

        return 0, 0, 1, 1

    def find_focused_view(self):
        for _, view in self._views.items():
            if view.up_state.is_focused:
                return view

        return None

    def get_extent(self):
        if len(self._views) == 0:
            return self.state.i, self.state.j, \
                self.state.i + self.state.size - 1, \
                self.state.j + self.state.size - 1

        min_i = min([view.state.i for _, view in self._views.items() if view.is_window()])
        min_j = min([view.state.j for _, view in self._views.items() if view.is_window()])
        max_i = max([view.state.i + view.state.w - 1 for _, view in self._views.items() if view.is_window()])
        max_j = max([view.state.j + view.state.h - 1 for _, view in self._views.items() if view.is_window()])

        """
        Borders around, such that views can be at the edges
        """
        min_i -= max(self.state.size - 1, 1)
        min_j -= max(self.state.size - 1, 1)
        max_i += max(self.state.size - 1, 1)
        max_j += max(self.state.size - 1, 1)

        return min_i, min_j, max_i, max_j

    def place_initial(self, view, w, h):
        place_i = 0
        place_j = 0
        for j, i in product(range(math.floor(self.state.j),
                                  math.ceil(self.state.j + self.state.size)),
                            range(math.floor(self.state.i),
                                  math.ceil(self.state.i + self.state.size))):
            for jp, ip in product(range(j, j + h), range(i, i + w)):
                if self.find_at_tile(ip, jp) is not None:
                    break
            else:
                place_i, place_j = i, j
                break
        else:
            place_i, place_j = self.state.i, self.state.j
            while self.find_at_tile(place_i, place_j) is not None:
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



    def reset_extent(self, focus_view=None):
        new_state = self.state.copy()
        new_state.min_i, new_state.min_j, new_state.max_i, new_state.max_j = \
            self.get_extent()

        print("Resetting extent: %d %d %d %d" % (new_state.min_i, new_state.min_j, new_state.max_i, new_state.max_j))

        if focus_view is None:
            self.animate_to(new_state)
        else:
            self.focus_view(focus_view, new_state)


    def move(self, delta_i, delta_j):
        i, j, w, h = self.find_focused_box()
        ci, cj = i + w/2., j + h/2.

        if ((i + w > self.state.i + self.state.size and delta_i > 0) or
                (i < self.state.i and delta_i < 0) or
                (j + h > self.state.j + self.state.size and delta_j > 0) or
                (j < self.state.j and delta_j < 0)):

            vf = None
            for _, v in self._views.items():
                if v.up_state.is_focused():
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


    def focus_view(self, view, new_state=None):
        view.focus()

        i, j, w, h = view.state.i, view.state.j, \
            view.state.w, view.state.h

        target_i, target_j, target_size = self.state.i, \
            self.state.j, self.state.size

        target_size = max(target_size, w, h)
        target_i = min(target_i, i)
        target_j = min(target_j, j)
        target_i = max(target_i, i + w - target_size)
        target_j = max(target_j, j + h - target_size)

        if new_state is None:
            new_state = self.state.copy()
            new_state.i = target_i
            new_state.j = target_j
            new_state.size = target_size
            new_state.scale = new_state.size * (.5 if self.is_half_scale else 1.)

            if new_state.i != self.state.i or new_state.j != self.state.j or new_state.size != self.state.size:
                if self.state.padding == 0:
                    new_state.padding = self.default_padding

        self.animate_to(new_state)

    # def toggle_half_scale(self):
    #     self.is_half_scale = not self.is_half_scale
    #     self.rescale()
    #     self.update(finished=True)

    def get_scale(self, state):
        return state.size * (.5 if self.is_half_scale else 1.)


    def toggle_padding(self):
        padding = self.default_padding \
            if self.state.padding == 0 else 0

        if padding == 0:
            for _, v in self._views.items():
                if v.is_window():
                    v.set_fullscreen(True)

            focused = self.find_focused_box()
            self.fullscreen_backup = self.state.i, self.state.j, \
                self.state.size

            new_state = self.state.copy()
            new_state.padding = padding
            new_state.i = focused[0]
            new_state.j = focused[1]
            new_state.size = max(focused[2:])
            new_state.scale = int(new_state.size / self.state.size * self.state.scale)

            self.animate_to(new_state)

        else:
            for _, v in self._views.items():
                if v.is_window():
                    v.set_fullscreen(False)


            new_state = self.state.copy()
            new_state.padding = padding
            if self.fullscreen_backup:
                reset = self.fullscreen_backup
                min_i, min_j, max_i, max_j = self.get_extent()
                if reset[0] >= min_i and reset[1] >= min_j \
                        and reset[0] + reset[2] - 1 <= max_i \
                        and reset[1] + reset[2] - 1 <= max_j:
                    new_state.i=reset[0]
                    new_state.j=reset[1]
                    new_state.size=reset[2]

                self.fullscreen_backup = None

            new_state.scale = int(new_state.size / self.state.size * self.state.scale)

            self.animate_to(new_state)


