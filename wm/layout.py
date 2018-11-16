import math
import os
from itertools import product

from pywm import (
    PyWM,
    PYWM_MOD_ALT,
    PYWM_MOD_LOGO,
    PYWM_MOD_CTRL,
    PYWM_RELEASED,
    PYWM_PRESSED,
)

from .background import Background
from .view import View, ViewState
from .state import State
from .animate import Animate


class Overview:
    def __init__(self, layout):
        self.layout = layout
        self.state = self.layout.state.copy()

        """
        Enlarge view port and recenter
        """
        self.state.i -= .5*(1.5 - 1.)*self.state.size
        self.state.j -= .5*(1.5 - 1.)*self.state.size
        self.state.size *= 1.5
        self.state.background_factor *= 1.5

    def get_initial_state(self):
        return self.state

    def get_final_state(self):
        new_state = self.state.copy()
        new_state.size = round(new_state.size / 1.5)
        new_state.background_factor /= 1.5
        new_state.i = round(new_state.i)
        new_state.j = round(new_state.j)
        return self.state, new_state

    def init(self):
        pass

    def destroy(self):
        pass

    def on_motion(self, delta_x, delta_y):
        self.state.i -= self.state.size * delta_x
        self.state.j -= self.state.size * delta_y
        self.layout.update(self.state)

    def on_axis(self, orientation, delta):
        self.state.i -= .5*0.01*delta
        self.state.j -= .5*0.01*delta
        self.state.size += 0.01*delta
        self.layout.update(self.state)


class LayoutState(State):
    def __init__(self, i, j, size, min_i, min_j, max_i, max_j, padding,
                 background_factor):
        super().__init__(['i', 'j', 'size',
                          'min_i', 'min_j', 'max_i', 'max_j',
                          'padding', 'background_factor'])

        self.i = i
        self.j = j
        self.size = size
        self.min_i = min_i
        self.min_j = min_j
        self.max_i = max_i
        self.max_j = max_j
        self.padding = padding
        self.background_factor = background_factor

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

        self.default_padding = 0.01
        self.state = LayoutState(0, 0, 2, 0, 0, 1, 1, self.default_padding, 3)
        self.overview = None

        self.background = None

        """
        scale == size: pixel-to-pixel
        scale == 2 * size: client-side width height are twice as
            high as rendered width, height => Appears half as big
        ...
        """
        self.is_half_scale = False
        self.scale = 2

    def update(self, state):
        for v in self.views:
            v.update(v.state, state)

        if self.background is not None:
            self.background.update(state, self.background.state)

    def find_at_tile(self, i, j):
        for view in self.views:
            if (view.state.i <= i < view.state.i + view.state.w) and \
                    (view.state.j <= j < view.state.j + view.state.h):
                return view

        return None

    def find_focused_box(self):
        for view in self.views:
            if view.focused:
                return view.state.i, view.state.j, view.state.w, view.state.h

        return 0, 0, 1, 1

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

        self.focus_view(view, new_state)

    def on_key(self, time_msec, keycode, state, keysyms):
        """
        All events with  our modifier are consumed.
        No events without our modifier are consumed.
        """
        if not self.modifiers & PYWM_MOD_LOGO:
            if self.overview is not None:
                self.exit_overview()
                return True
            return False

        if state == PYWM_PRESSED:
            if keysyms == "h":
                if self.modifiers & PYWM_MOD_CTRL:
                    self.resize_view(-1, 0)
                else:
                    self.move(-1, 0)
            elif keysyms == "H":
                self.move_view(-1, 0)
            elif keysyms == "l":
                if self.modifiers & PYWM_MOD_CTRL:
                    self.resize_view(1, 0)
                else:
                    self.move(1, 0)
            elif keysyms == "L":
                self.move_view(1, 0)
            elif keysyms == "k":
                if self.modifiers & PYWM_MOD_CTRL:
                    self.resize_view(0, -1)
                else:
                    self.move(0, -1)
            elif keysyms == "K":
                self.move_view(0, -1)
            elif keysyms == "j":
                if self.modifiers & PYWM_MOD_CTRL:
                    self.resize_view(0, 1)
                else:
                    self.move(0, 1)
            elif keysyms == "J":
                self.move_view(0, 1)
            elif keysyms == "Return":
                os.system("termite &")
            elif keysyms == "C":
                self.terminate()
            elif keysyms == "a":
                self.enter_overview()
            elif keysyms == "s":
                self.toggle_half_scale()
            elif keysyms == "f":
                self.toggle_padding()

        return True

    def on_modifiers(self, modifiers):
        if not self.modifiers & PYWM_MOD_ALT:
            if self.overview is not None:
                self.exit_overview()
                return True
        return False

    def move(self, delta_i, delta_j):
        i, j, w, h = self.find_focused_box()
        ci, cj = i + w/2., j + h/2.

        def score(view):
            cvi, cvj = view.state.i + view.state.w/2., \
                view.state.j + view.state.h/2.
            sp = (cvi - ci) * delta_i + (cvj - cj) * delta_j
            sp *= ((cvi - ci) ** 2) + ((cvj - cj) ** 2)
            return sp

        best_view = None
        best_view_score = 1000

        for view in self.views:
            s = score(view)
            if s > 0. and s < best_view_score:
                best_view_score = s
                best_view = view

        if best_view is not None:
            self.focus_view(best_view)

    def box_intersects(self, box1, box2):
        box1_tiles = []
        for i, j in product(range(math.floor(box1[0]), math.ceil(box1[0] + box1[2])),
                            range(math.floor(box1[1]), math.ceil(box1[1] + box1[3]))):
            box1_tiles += [(i, j)]

        box2_tiles = []
        for i, j in product(range(math.floor(box2[0]), math.ceil(box2[0] + box2[2])),
                            range(math.floor(box2[1]), math.ceil(box2[1] + box2[3]))):
            box2_tiles += [(i, j)]

        for t in box1_tiles:
            if t in box2_tiles:
                return True
        return False

    def move_view(self, delta_i, delta_j):
        view = [v for v in self.views if v.focused]
        if len(view) == 0:
            return
        view = view[0]
        new_view_box = view.state.i + delta_i, \
            view.state.j + delta_j, view.state.w, view.state.h

        for v in self.views:
            if v == view:
                continue
            if self.box_intersects(new_view_box, [v.state.i, v.state.j,
                                                  v.state.w, v.state.h]):
                return

        new_view_state = view.state.copy()
        new_view_state.i = new_view_box[0]
        new_view_state.j = new_view_box[1]
        new_view_state.w = new_view_box[2]
        new_view_state.h = new_view_box[3]

        view.transition(new_view_state, .2)

    def resize_view(self, delta_i, delta_j):
        view = [v for v in self.views if v.focused]
        if len(view) == 0:
            return
        view = view[0]
        new_view_box = view.state.i, view.state.j, \
            view.state.w + delta_i, view.state.h + delta_j

        while new_view_box[2] <= 0:
            new_view_box[2] += 1
            new_view_box[0] -= 1

        while new_view_box[3] <= 0:
            new_view_box[3] += 1
            new_view_box[1] -= 1

        for v in self.views:
            if v == view:
                continue
            if self.box_intersects(new_view_box, [v.state.i, v.state.j,
                                                  v.state.w, v.state.h]):
                return

        new_view_state = view.state.copy()
        new_view_state.i = new_view_box[0]
        new_view_state.j = new_view_box[1]
        new_view_state.w = new_view_box[2]
        new_view_state.h = new_view_box[3]

        if view.transition(new_view_state, .2):
            view.update_dimensions(new_view_state)

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

        self.transition(new_state, .2)

    def toggle_half_scale(self):
        self.is_half_scale = not self.is_half_scale
        self.rescale()

    def rescale(self):
        self.scale = self.state.size * (.5 if self.is_half_scale else 1.)
        for v in self.views:
            v.update_dimensions()

    def toggle_padding(self):
        new_state = self.state.copy()
        new_state.padding = self.default_padding \
            if new_state.padding == 0 else 0

        self.transition(new_state, .2)

    def enter_overview(self):
        if self.overview is not None:
            return

        ovr = Overview(self)
        new_state = ovr.get_initial_state()
        if self.transition(new_state, .2):
            self.overview = ovr
            self.overview.init()

    def exit_overview(self):
        if self.overview is None:
            return

        state, new_state = self.overview.get_final_state()
        self.state = state
        if self.transition(new_state, .2):
            self.overview.destroy()
            self.overview = None
            self.rescale()
            self.update_cursor()

    def on_motion(self, time_msec, delta_x, delta_y):
        if self.overview is not None:
            self.overview.on_motion(delta_x, delta_y)
            return True

        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        if self.overview is not None:
            self.overview.on_axis(orientation, delta)
            return True

        return False

    def main(self):
        self.background = self.create_widget(Background,
                                             '/home/jonas/wallpaper.jpg')
        self.background.update(self.state, self.background.state)
