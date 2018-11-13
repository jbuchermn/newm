import os
import time
import traceback
from threading import Thread
from abc import abstractmethod
from itertools import product

from pywm import (
    PyWM,
    PyWMView,
    PyWMWidget,
    PYWM_MOD_CTRL,
    PYWM_PRESSED,
    PYWM_LAYER_BACK,
    PYWM_FORMATS
)


class Animation:
    def __init__(self, target, prop, func, final):
        self._target = target
        self._prop = prop
        self._func = func
        self._final = final

    def set(self, ts):
        self._target.__dict__[self._prop] = self._func(ts)

    def set_final(self):
        self._target.__dict__[self._prop] = self._final


class InterAnimation:
    def __init__(self, target, prop, delta):
        self._target = target
        self._prop = prop
        self._initial = None
        self._delta = delta

    def set(self, ts):
        if self._initial is None:
            self._initial = self._target.__dict__[self._prop]
        self._target.__dict__[self._prop] = self._initial + \
            ts * self._delta

    def set_final(self):
        self._target.__dict__[self._prop] = self._initial + self._delta


class FinalAnimation:
    def __init__(self, target, prop, delta):
        self._target = target
        self._prop = prop
        self._initial = None
        self._delta = delta

    def set(self, ts):
        if self._initial is None:
            self._initial = self._target.__dict__[self._prop]

    def set_final(self):
        self._target.__dict__[self._prop] = self._initial + self._delta


class AnimateThread(Thread):
    def __init__(self, parent, targets, animations, duration):
        super().__init__()
        self._parent = parent
        self._targets = targets
        self._animations = animations
        self._duration = duration
        self.finished = False

    def run(self):
        initial = time.time()
        ts = initial
        while ts < initial + self._duration:
            for anim in self._animations:
                anim.set((ts - initial)/self._duration)
            for target in self._targets:
                target.update()

            time.sleep(0.02)

            ts = time.time()

        for anim in self._animations:
            anim.set_final()
        for target in self._targets:
            target.update()
        self.finished = True
        self._parent.animation_finished()


class Animate:
    def __init__(self):
        self._current_animation = None
        self._pending_animation = None

    @abstractmethod
    def update(self):
        pass

    def animation_finished(self):
        if self._pending_animation is not None:
            self._current_animation = self._pending_animation
            self._pending_animation = None
            self._current_animation.start()

    def animate(self, animations, duration):
        anim = AnimateThread(self, [self], animations, duration)
        if self._current_animation is not None:
            if not self._current_animation.finished:
                self._pending_animation = anim
                return

        self._current_animation = anim
        self._current_animation.start()


class View(PyWMView):
    def __init__(self, wm, handle):
        super().__init__(wm, handle)

        """
        Position, width and height in terms of tiles
        """
        self.i = 0
        self.j = 0
        self.w = 0
        self.h = 0

        self.wm.place_initial(self)
        self.focus()

    def update(self):
        if self.w <= 0:
            self.w = 1
        if self.h <= 0:
            self.h = 1

        i = self.i
        j = self.j
        w = self.w
        h = self.h

        x = i - self.wm.i + self.wm.padding
        y = j - self.wm.j + self.wm.padding

        w -= 2*self.wm.padding
        h -= 2*self.wm.padding

        x *= self.wm.width / self.wm.size
        y *= self.wm.height / self.wm.size
        w *= self.wm.width / self.wm.size
        h *= self.wm.height / self.wm.size

        width = round(w * self.wm.size / self.wm.scale)
        height = round(h * self.wm.size / self.wm.scale)

        self.set_box(x, y, w, h)
        if (width, height) != self.get_dimensions():
            self.set_dimensions(width, height)


class Layout(PyWM, Animate):
    def __init__(self):
        PyWM.__init__(self, View)
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

    def find_at_tile(self, i, j):
        for view in self.views:
            if (view.i <= i < view.i + view.w) and \
                    (view.j <= j < view.j + view.h):
                return view

        return None

    def place_initial(self, view):
        for i, j in product(range(self.i, self.i + self.size),
                            range(self.j, self.j + self.size)):
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
        view.update()

    def update(self):
        if self.size <= 0:
            self.size = 1
        if self.scale <= 0:
            self.scale = 1

        for v in self.views:
            v.update()

    def on_key(self, time_msec, keycode, state, keysyms):
        if not self.modifiers & PYWM_MOD_CTRL:
            return False

        if state != PYWM_PRESSED:
            return True

        if keysyms == "Left":
            self.animate([InterAnimation(self, 'i', -1)], 0.2)
        elif keysyms == "Right":
            self.animate([InterAnimation(self, 'i', +1)], 0.2)
        elif keysyms == "Up":
            self.animate([InterAnimation(self, 'j', -1)], 0.2)
        elif keysyms == "Down":
            self.animate([InterAnimation(self, 'j', +1)], 0.2)
        elif keysyms == "Return":
            os.system("termite &")
        elif keysyms == "C":
            self.terminate()
        elif keysyms == "a":
            self.animate([
                InterAnimation(self, 'size', +1),
                FinalAnimation(self, 'scale', +1)], 0.2)
        elif keysyms == "s":
            self.animate([
                InterAnimation(self, 'size', -1),
                FinalAnimation(self, 'scale', -1)], 0.2)
        else:
            print(keysyms)

        return True


main = Layout()


try:
    print("Running...")
    main.start()

    widget = main.create_widget(PyWMWidget)
    widget.set_box(0, 0, 500, 500)
    widget.set_layer(PYWM_LAYER_BACK)

    data = bytearray(4 * 500 * 500)
    for i in range(len(data)):
        data[i] = (7*i) % 256
    widget.set_pixels(PYWM_FORMATS['ARGB8888'], 500, 500, 500, bytes(data))

    while True:
        time.sleep(1)

except Exception:
    traceback.print_exc()

finally:
    print("Terminating...")
    main.terminate()
