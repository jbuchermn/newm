import time

from pywm import PyWMBackgroundWidget, PyWMWidgetDownstreamState

from ..interpolation import WidgetDownstreamInterpolation
from ..animate import Animate


class Background(PyWMBackgroundWidget, Animate):
    def __init__(self, wm, path):
        PyWMBackgroundWidget.__init__(self, wm, path)
        Animate.__init__(self)

    def reducer(self, wm_state):
        result = PyWMWidgetDownstreamState()
        result.z_index = -100
        result.opacity = wm_state.background_opacity

        min_i, min_j, max_i, max_j = wm_state.get_extent()

        """
        Possibly extend bounds
        """
        min_i = min(min_i, wm_state.i)
        min_j = min(min_j, wm_state.j)
        max_i = max(max_i, min_i + wm_state.size - 1)
        max_j = max(max_j, min_j + wm_state.size - 1)

        """
        Box of background
        """
        x = min_i - 1
        y = min_j - 1
        w = (max_i - min_i + 3)
        h = (max_j - min_j + 3)
        w, h = max(w, h), max(w, h)

        """
        Box of viewport
        """
        vp_x = wm_state.i
        vp_y = wm_state.j
        vp_w = wm_state.size
        vp_h = wm_state.size

        """
        Enlarge box and viewport
        """
        factor = wm_state.background_factor

        cx = x + w/2
        cy = y + h/2
        x = cx - factor/2.*w
        y = cy - factor/2.*h
        w = factor*w
        h = factor*h

        vp_cx = vp_x + vp_w/2
        vp_cy = vp_y + vp_h/2
        vp_x = vp_cx - factor/2.*vp_w
        vp_y = vp_cy - factor/2.*vp_h
        vp_w = factor*vp_w
        vp_h = factor*vp_h

        """
        Transform such that viewport has
        x, y == 0; w == wm.width; h == wm.height
        """
        m = self.wm.width / vp_w
        b = - vp_x * m
        x, w = (m * x + b), (m * (x + w) + b)
        w -= x

        m = self.wm.height / vp_h
        b = - vp_y * m
        y, h = (m * y + b), (m * (y + h) + b)
        h -= y

        """
        Fix aspect ratio
        """
        if w/h > self.width/self.height:
            new_h = self.height * w/self.width
            y -= (new_h - h)/2.
            h = new_h
        else:
            new_w = self.width * h/self.height
            x -= (new_w - w)/2.
            w = new_w

        result.box = (x, y, w, h)
        return result

    def animate(self, old_state, new_state, dt):
        cur = self.reducer(old_state)
        nxt = self.reducer(new_state)

        self._animate(WidgetDownstreamInterpolation(cur, nxt), dt)

    def process(self):
        return self._process(self.reducer(self.wm.state))
