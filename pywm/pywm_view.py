from ._pywm import (
    view_get_box,
    view_get_dimensions,
    view_get_title_app_id,
    view_set_box,
    view_set_dimensions,
    view_focus
)


class PyWMView:
    def __init__(self, wm, handle):
        self._handle = handle

        """
        Consider these readonly
        """
        self.wm = wm
        self.box = view_get_box(self._handle)
        self.title, self.app_id = view_get_title_app_id(self._handle)

    def focus(self):
        view_focus(self._handle)

    def set_box(self, x, y, w, h):
        view_set_box(self._handle, x, y, w, h)
        self.box = (x, y, w, h)

    def get_dimensions(self):
        return view_get_dimensions(self._handle)

    def set_dimensions(self, width, height):
        view_set_dimensions(self._handle, round(width), round(height))

    """
    Virtual methods
    """

    def destroy(self):
        pass
