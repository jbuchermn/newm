from ._pywm import (
    widget_create,
    widget_destroy,
    widget_set_box,
    widget_set_layer,
    widget_set_pixels
)


PYWM_LAYER_BACK = 0
PYWM_LAYER_FRONT = 0

PYWM_FORMATS = dict()

with open('/usr/include/wayland-server-protocol.h', 'r') as header:
    started = False
    for r in header:
        data = r.replace(" ", "").replace("\t", "").replace(",", "").split("=")
        if data[0].startswith('WL_SHM_FORMAT_'):
            name = data[0][14:]
            code = int(data[1], 0)

            PYWM_FORMATS[name] = code


class PyWMWidget:
    def __init__(self, wm):
        self._handle = widget_create()

        """
        Consider these readonly
        """
        self.wm = wm
        self.box = (0, 0, 0, 0)
        self.layer = PYWM_LAYER_BACK

    def set_box(self, x, y, w, h):
        widget_set_box(self._handle, x, y, w, h)
        self.box = (x, y, w, h)

    def set_layer(self, layer):
        widget_set_layer(self._handle, layer)
        self.layer = layer

    def destroy(self):
        widget_destroy(self._handle)
        self.wm.on_widget_destroy(self)

    def set_pixels(self, fmt, stride, width, height, data):
        widget_set_pixels(self._handle, fmt, stride, width, height, data)

