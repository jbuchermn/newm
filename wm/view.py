from pywm import PyWMView


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

        self.client_side_scale = 1.
        _, _, _, xwayland = self.get_info()
        if xwayland:
            """
            X cleints are responsible to handle
            HiDPI themselves
            """
            self.client_side_scale = self.wm.config['output_scale']

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

        width = round(w * self.wm.size / self.wm.scale *
                      self.client_side_scale)
        height = round(h * self.wm.size / self.wm.scale *
                       self.client_side_scale)

        self.set_box(x, y, w, h)
        if (width, height) != self.get_dimensions():
            self.set_dimensions(width, height)
