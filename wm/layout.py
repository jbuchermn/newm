import math
import os
from itertools import product

from pywm import (
    PyWM,
    PYWM_MOD_LOGO,
    PYWM_MOD_CTRL,
    PYWM_PRESSED,
)

from .background import Background
from .view import View
from .animate import Animate, InterAnimation


class Layout(PyWM, Animate):
    def __init__(self, **kwargs):
        PyWM.__init__(self, View, **kwargs)
        Animate.__init__(self)

        """
        Position (index of top-left visible tile) and size
        (2x2 tiles, 3x3 tiles, ...) in terms of tiles
        """
        self.i = 0
        self.j = 0
        self.size = 2

        """
        padding at scale == 0 in terms of tiles
        """
        self.padding = 0.01

        """
        size <  scale => width, height <  w, h
        size == scale => width, height == w, h
        size >  scale => width, height >  w, h
        """
        self.scale = 2

        self.overview = False

    def find_at_tile(self, i, j):
        for view in self.views:
            if (view.i <= i < view.i + view.w) and \
                    (view.j <= j < view.j + view.h):
                return view

        return None

    def get_extent(self):
        if len(self.views) == 0:
            return 0, 0, 0, 0

        min_i = min([view.i for view in self.views])
        min_j = min([view.j for view in self.views])
        max_i = max([view.i for view in self.views])
        max_j = max([view.j for view in self.views])

        return min_i, min_j, max_i, max_j

    def place_initial(self, view):
        for i, j in product(range(math.floor(self.i),
                                  math.ceil(self.i + self.size)),
                            range(math.floor(self.j),
                                  math.ceil(self.j + self.size))):
            if self.find_at_tile(i, j) is None:
                view.i, view.j = i, j
                break
        else:
            i, j = self.i, self.j
            while self.find_at_tile(i, j) is not None:
                i += 1
            view.i = i
            view.j = j

        view.w = 1
        view.h = 1

    def on_new_view(self, view):
        view.update()
        self.background.update()

    def update(self):
        if self.size <= 0:
            self.size = 1
        if self.scale <= 0:
            self.scale = 1

        for v in self.views:
            v.update()

        self.background.update()
        if not self.overview:
            self.update_cursor()

    def on_key(self, time_msec, keycode, state, keysyms):
        if not self.modifiers & PYWM_MOD_CTRL:
            return False

        if state != PYWM_PRESSED:
            if self.overview:
                self.i = round(self.i)
                self.j = round(self.j)
                self.size /= 1.5
                self.overview = False
                self.update()
            return True

        if keysyms == "h":
            self.animate([InterAnimation(self, 'i', -1)], 0.2)
        elif keysyms == "l":
            self.animate([InterAnimation(self, 'i', +1)], 0.2)
        elif keysyms == "k":
            self.animate([InterAnimation(self, 'j', -1)], 0.2)
        elif keysyms == "j":
            self.animate([InterAnimation(self, 'j', +1)], 0.2)
        elif keysyms == "Return":
            os.system("termite &")
        elif keysyms == "C":
            self.terminate()
        elif keysyms == "a":
            self.animate([
                InterAnimation(self, 'size', self.size)], 0.2)
        elif keysyms == "s":
            self.animate([
                InterAnimation(self, 'size', -self.size/2.)], 0.2)
        elif keysyms == "d":
            self.animate([
                InterAnimation(self, 'scale', self.scale)], 0.2)
        elif keysyms == "f":
            self.animate([
                InterAnimation(self, 'scale', -self.scale/2.)], 0.2)
        elif keysyms == "y":
            if not self.overview:
                self.overview = True
                self.size *= 1.5
                self.update()
        else:
            print(keysyms)

        return True

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
