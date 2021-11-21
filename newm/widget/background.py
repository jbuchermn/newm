from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

import time
import logging
import numpy as np

from pywm import PyWMBackgroundWidget, PyWMWidgetDownstreamState, PyWMOutput

from ..interpolation import WidgetDownstreamInterpolation
from ..animate import Animate

if TYPE_CHECKING:
    from ..state import LayoutState
    from ..layout import Layout, Workspace, WorkspaceState

logger = logging.getLogger(__name__)

class BackgroundState:
    def __init__(self, layout_state: LayoutState, ws_state: WorkspaceState) -> None:
        x1, y1, x2, y2 = ws_state.get_extent()
        x2 += 1
        y2 += 1

        vx1, vy1, vx2, vy2 = ws_state.i, ws_state.j, ws_state.size, ws_state.size

        self.extent = np.array([x1, y1, x2 - x1, y2 - y1], dtype=np.float64)
        self.viewpoint = np.array([vx1, vy1, vx2, vy2], dtype=np.float64)

        self.opacity = layout_state.background_opacity

    def delta(self, other: BackgroundState) -> float:
        return np.linalg.norm(self.extent - other.extent) + np.linalg.norm(self.viewpoint - other.viewpoint) + abs(self.opacity - other.opacity)

    def approach(self, other: BackgroundState, time_scale: float, dt: float) -> None:
        de = other.extent - self.extent
        dv = other.viewpoint - self.viewpoint
        do = other.opacity - self.opacity
        factor = min(1, dt / time_scale)

        self.extent += de*factor
        self.viewpoint += dv*factor
        self.opacity += do*factor

    def __str__(self) -> str:
        return "<BackgroundState extent=%s viewpoint=%s>" % (str(self.extent), str(self.viewpoint))


class Background(PyWMBackgroundWidget):
    def __init__(self, wm: Layout, output: PyWMOutput, workspace: Workspace, path: str):
        PyWMBackgroundWidget.__init__(self, wm, output, path)

        self._output: PyWMOutput = output
        self._workspace: Workspace = workspace

        self._current_state = BackgroundState(self.wm.state, self.wm.state.get_workspace_state(self._workspace))
        self._target_state = BackgroundState(self.wm.state, self.wm.state.get_workspace_state(self._workspace))
        self._last_frame: float = time.time()
        self._anim_caught: Optional[float] = None


    def animate(self, old_state: LayoutState, new_state: LayoutState, dt: float) -> None:
        self._anim_caught = time.time() + dt
        self._target_state = BackgroundState(new_state, new_state.get_workspace_state(self._workspace))

        self._last_frame = time.time()
        self.damage()

    def process(self) -> PyWMWidgetDownstreamState:
        # State handling
        t = time.time()

        if self._anim_caught is not None:
            if t > self._anim_caught:
                self._anim_caught = None
        else:
            target_state = BackgroundState(self.wm.state, self.wm.state.get_workspace_state(self._workspace))
            if target_state.delta(self._target_state) > 0.001:
                self._target_state = target_state

        if self._current_state.delta(self._target_state) >= 0.001:
            self._current_state.approach(self._target_state, .25, t - self._last_frame)
            self.damage()

        self._last_frame = t

        # Positioning
        result = PyWMWidgetDownstreamState()
        result.z_index = -10000
        result.opacity = self._current_state.opacity

        # Set pos_x, pos_y, width, height of screen in coordinates of wallpaper
        vx, vy, vw, vh = self._current_state.viewpoint
        ex, ey, ew, eh = self._current_state.extent

        vx -= ex
        vy -= ey
        # ex, ey == 0, 1

        vx /= ew
        vy /= eh
        vw /= ew
        vh /= eh
        # ew, eh == 1, 1

        vw = min(1, vw)
        vh = min(1, vh)
        vx = max(0, min(1 - vw, vx))
        vy = max(0, min(1 - vh, vy))
        # vx, vy, vw, vh are viewport within [0, 1] x [0, 1]

        vx *= self.width
        vy *= self.height
        vw *= self.width
        vh *= self.height
        # vx, vy, vw, vh are viewport within image resolution

        w0 = self.width / ew
        h0 = self.height / eh
        w1 = self._output.width * self._output.scale
        h1 = self._output.height * self._output.scale
        if abs(w0 - self.width) > 0.1 and abs(h0 - self.height) > 0.1:
            vwp = self.width + (w1 - self.width) / (w0 - self.width) * (vw - self.width)
            vhp = self.height + (h1 - self.height) / (h0 - self.height) * (vh - self.height)
            # vwp, vhp are target size in same coordiantes as vx, vy, vw, vh

            if abs(vw - vwp) < 0.1 or abs(vh - vhp) < 0.1:
                vxp = vx
                vyp = vy
            else:
                vxp = (self.width - vwp) / (self.width - vw) * vx
                vyp = (self.height - vhp) / (self.height - vh) * vy
            # vxp, vyp are corresponding coordinates

        else:
            vxp, vyp, vwp, vhp = vx, vy, vw, vh

        x, y, w, h = vxp, vyp, vwp, vhp
        if w/h < self._output.width/self._output.height:
            new_h = self._output.height * w/self._output.width
            y -= (new_h - h)/2.
            h = new_h
        else:
            new_w = self._output.width * h/self._output.height
            x -= (new_w - w)/2.
            w = new_w
        # x, y, w, h are possibly shrinked to account for aspect ratio

        if w < w1 or h < h1:
            logger.debug("Background scaling issue: %dx%d on %dx%d wallpaper" % (w, h, self.width, self.height))

        fx, fy = -x * self._output.width / w, -y * self._output.height / h
        fw, fh = self.width * self._output.width / w, self.height * self._output.height / h
        # fx, fy, fw, fh are transformed to output coordinates

        if self.height > 0 and abs(fw / fh - self.width / self.height) > 0.01:
            logger.debug("Background aspect ratio issue: %dx%d on %dx%d wallpaper" % (fw, fh, self.width, self.height))

        result.box = (self._output.pos[0] + fx, self._output.pos[1] + fy, fw, fh)
        return result
