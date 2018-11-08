import time

from pywm import PyWM, PyWMView


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

    def update(self):
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
            print(width, height, self.get_dimensions())
            self.set_dimensions(width, height)


class Layout(PyWM):
    def __init__(self):
        super().__init__(View)

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
        i, j = 0, 0
        w, h = 1, 1
        while self.find_at_tile(i, j) is not None:
            i += 1

        view.i = i
        view.j = j
        view.w = w
        view.h = h
        view.update()

    def update(self):
        for v in self.views:
            v.update()

    def on_key(self, time_msec, keycode, state):
        if state == 0:
            return False

        if keycode == 30:
            self.scale += 1
            self.update()
            return True
        elif keycode == 31:
            self.scale -= 1
            self.update()
            return True
        elif keycode == 32:
            self.size += 1
            self.update()
            return True
        elif keycode == 33:
            self.size -= 1
            self.update()
            return True

        return False


main = Layout()

print("Running...")
main.run()

try:
    while True:
        time.sleep(1)
finally:
    print("Terminating...")
    main.terminate()
