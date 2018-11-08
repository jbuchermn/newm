class PyWMView:
    def __init__(self, wm, handle):
        self._handle = handle
        self.wm = wm
        self.box = view_get_box(self._handle)

    def set_box(self, x, y, w, h):
        view_set_box(self._handle, x, y, w, h)
        self.box = (x, y, w, h)

    def get_dimensions(self):
        return view_get_dimensions(self._handle)

    def set_dimensions(self, width, height):
        view_set_dimensions(self._handle, round(width), round(height))

    def destroy(self):
        pass
