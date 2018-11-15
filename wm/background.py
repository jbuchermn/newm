from pywm import PyWMBackgroundWidget


class Background(PyWMBackgroundWidget):
    def __init__(self, wm, path):
        super().__init__(wm, path)

    def update(self):
        min_i, min_j, max_i, max_j = self.wm.get_extent()
        w = 2 * (max_i - min_i + 1) / self.wm.size * self.wm.width
        h = 2 * (max_j - min_j + 1) / self.wm.size * self.wm.height
        x = - .2 * (self.wm.i - min_i + 3) / self.wm.size * self.wm.height
        y = - .2 * (self.wm.j - min_j + 3) / self.wm.size * self.wm.height
        self.set_box(x, y, w, h)
