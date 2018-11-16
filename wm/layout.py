import math
import os
from itertools import product

from pywm import (
    PyWM,
    PYWM_MOD_ALT,
    PYWM_MOD_LOGO,
    PYWM_MOD_CTRL,
    PYWM_RELEASED,
)

from .background import Background
from .view import View, ViewState
from .state import State
from .animate import Animate


class LayoutState(State):
    def __init__(self, i, j, size, min_i, min_j, max_i, max_j, padding):
        super().__init__(['i', 'j', 'size',
                          'min_i', 'min_j', 'max_i', 'max_j',
                          'padding'])

        self.i = i
        self.j = j
        self.size = size
        self.min_i = min_i
        self.min_j = min_j
        self.max_i = max_i
        self.max_j = max_j
        self.padding = padding

    def lies_within_extent(self, i, j):
        if i < self.min_i:
            return False
        if j < self.min_j:
            return False
        if i + self.size - 1 > self.max_i:
            return False
        if j + self.size - 1 > self.max_j:
            return False

        return True


class Layout(PyWM, Animate):
    def __init__(self, **kwargs):
        PyWM.__init__(self, View, **kwargs)
        Animate.__init__(self)

        self.state = LayoutState(0, 0, 2, 0, 0, 1, 1, 0.05)

        self.background = None

        """
        scale == size: pixel-to-pixel
        scale == 2 * size: client-side width height are twice as
            high as rendered width, height => Appears half as big
        ...
        """
        self.scale = 1
        self.overview = False

    def update(self, state):
        for v in self.views:
            v.update(state, v.state)

        if self.background is not None:
            self.background.update(state, self.background.state)

    def find_at_tile(self, i, j):
        for view in self.views:
            if (view.state.i <= i < view.state.i + view.state.w) and \
                    (view.state.j <= j < view.state.j + view.state.h):
                return view

        return None

    def get_extent(self):
        if len(self.views) == 0:
            return self.state.i, self.state.j, \
                self.state.i + self.state.size - 1, \
                self.state.j + self.state.size - 1

        min_i = min([view.state.i for view in self.views])
        min_j = min([view.state.j for view in self.views])
        max_i = max([view.state.i for view in self.views])
        max_j = max([view.state.j for view in self.views])

        """
        Borders around, such that views can be at the edges
        """
        min_i -= self.state.size - 1
        min_j -= self.state.size - 1
        max_i += self.state.size - 1
        max_j += self.state.size - 1

        return min_i, min_j, max_i, max_j

    def place_initial(self, view):
        place_i = 0
        place_j = 0
        for j, i in product(range(math.floor(self.state.j),
                                  math.ceil(self.state.j + self.state.size)),
                            range(math.floor(self.state.i),
                                  math.ceil(self.state.i + self.state.size))):
            if self.find_at_tile(i, j) is None:
                place_i, place_j = i, j
                break
        else:
            place_i, place_j = self.state.i, self.state.j
            while self.find_at_tile(place_i, place_j) is not None:
                place_i += 1

        view.state = ViewState(place_i, place_j, 1, 1)
        view.update_dimensions()

        new_state = self.state.copy()
        new_state.min_i, new_state.min_j, new_state.max_i, new_state.max_j = \
            self.get_extent()

        self.transition(new_state, .2)

    def on_key(self, time_msec, keycode, state, keysyms):
        """
        All events with  our modifier are consumed.
        No events without our modifier are consumed.
        """
        if not self.modifiers & PYWM_MOD_ALT:
            return False

        if state == PYWM_RELEASED:
            if keysyms == "y":
                self.exit_overview()

        else:
            if keysyms == "h":
                self.move(-1, 0)
            elif keysyms == "l":
                self.move(1, 0)
            elif keysyms == "k":
                self.move(0, -1)
            elif keysyms == "j":
                self.move(0, 1)
            elif keysyms == "Return":
                os.system("termite &")
            elif keysyms == "C":
                self.terminate()
            elif keysyms == "a":
                self.enter_overview()

        return True


    def move(self, delta_i, delta_j):
        if not self.state.lies_within_extent(self.state.i + delta_i,
                                             self.state.j + delta_j):
            return

        new_state = self.state.copy()
        new_state.i += delta_i
        new_state.j += delta_j

        self.transition(new_state, .2)

    def enter_overview(self):
        pass

    def exit_overview(self):
        pass

    def on_motion(self, time_msec, delta_x, delta_y):
        if self.overview:
            self.i += -4 * delta_x / self.width
            self.j += -4 * delta_y / self.height
            self.update()
            return True

        return False

    def on_motion_absolute(self, time_msec, x, y):
        if self.overview:
            self.i = -4 * (x - 0.5)
            self.j = -4 * (y - 0.5)
            self.update()
            return True

        return False

    def main(self):
        self.background = self.create_widget(Background,
                                             '/home/jonas/wallpaper.jpg')
        self.background.update(self.state, self.background.state)
