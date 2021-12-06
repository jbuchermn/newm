from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, cast

import math
import time
import logging

from pywm import PyWMBackgroundWidget, PyWMWidgetDownstreamState, PyWMOutput

from ..interpolation import WidgetDownstreamInterpolation
from ..animate import Animate
from ..config import configured_value

if TYPE_CHECKING:
    from ..state import LayoutState
    from ..layout import Layout, Workspace, WorkspaceState

logger = logging.getLogger(__name__)

conf_outputs = configured_value('outputs', cast(list[dict[str, Any]], []))
conf_time_scale = configured_value('background.time_scale', 0.15)
conf_path_default = configured_value('background.path', cast(Optional[str], None))
conf_anim_default = configured_value('background.anim', True)

class BackgroundState:
    def __init__(self, layout_state: LayoutState, ws_state: WorkspaceState, wallpaper_size: tuple[int, int], output_size: tuple[float, float], output_scale: float) -> None:
        x1, y1, x2, y2 = ws_state.get_extent()
        x2 += 1
        y2 += 1

        x1 -= 1
        y1 -= 1
        x2 += 1
        y2 += 1

        vx, vy, vw, vh = ws_state.i, ws_state.j, ws_state.size, ws_state.size

        if vx < x1:
            vw -= (x1 - vx)
            vx = x1
        if vy < y1:
            vy -= (y1 - vy)
            vy = y1
        if vx + vw > x2:
            vw = (x2 - vx)
        if vy + vh > y2:
            vh = (y2 - vy)

        extent = x1, y1, x2 - x1, y2 - y1
        viewpoint = vx, vy, vw, vh
        opacity = layout_state.background_opacity

        vx, vy, vw, vh = viewpoint
        ex, ey, ew, eh = extent

        vx -= ex
        vy -= ey
        # 1. ex, ey == 0, 1

        vx /= ew
        vy /= eh
        vw /= ew
        vh /= eh
        # 2. ew, eh == 1, 1

        vw = min(1, vw)
        vh = min(1, vh)
        vx = max(0, min(1 - vw, vx))
        vy = max(0, min(1 - vh, vy))
        # 3. vx, vy, vw, vh are viewport within [0, 1] x [0, 1]

        width, height = wallpaper_size
        output_width, output_height = output_size
        vx *= width
        vy *= height
        vw *= width
        vh *= height
        # 4. vx, vy, vw, vh are viewport within image resolution

        # if vx < 0 or vx + vw > width or vy < 0 or vy + vh > height:
        #     logger.debug("Background placement issue vx vy vw vh = %f %f %f %f (%f %f)" % (vx, vy, vw, vh, width, height))

        w0 = width / ew
        h0 = height / eh
        w1 = output_width * output_scale
        h1 = output_height * output_scale
        if abs(w0 - width) > 0.1 and abs(h0 - height) > 0.1 and width > w1 and height > h1:
            vwp = width + (w1 - width) / (w0 - width) * (vw - width)
            vhp = height + (h1 - height) / (h0 - height) * (vh - height)
            # 5a. vwp, vhp are target size in same coordiantes as vx, vy, vw, vh

            if abs(vw - vwp) < 0.1 or abs(vh - vhp) < 0.1:
                vxp = vx
                vyp = vy
            else:
                vxp = (width - vwp) / (width - vw) * vx
                vyp = (height - vhp) / (height - vh) * vy
            # 5b. vxp, vyp are corresponding coordinates

        else:
            vxp, vyp, vwp, vhp = vx, vy, vw, vh

        # if vxp < 0 or vxp + vwp > width or vyp < 0 or vyp + vhp > height:
        #     logger.debug("Background placement issue vxp vyp vwp vhp = %f %f %f %f (%f %f)" % (vxp, vyp, vwp, vhp, width, height))

        x, y, w, h = vxp, vyp, vwp, vhp
        if w/h < output_width/output_height:
            new_h = output_height * w/output_width
            y -= (new_h - h)/2.
            h = new_h
        else:
            new_w = output_width * h/output_height
            x -= (new_w - w)/2.
            w = new_w
        # 6. x, y, w, h are possibly shrinked to account for aspect ratio

        # Safety net - should not be necessary
        scale_fac = 1.
        if w > width:
            scale_fac = width / w
        if h > height:
            scale_fac = min(scale_fac, height / h)
        w, h = scale_fac*w, scale_fac*h


        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x + w > width:
            x = width - w
        if y + h > height:
            y = height - h

        # if x < 0 or x + w > width or y < 0 or y + h > height:
        #     logger.debug("Background placement issue x y w h = %f %f %f %f (%f %f)" % (x, y, w, h, width, height))

        # if w < w1 or h < h1:
        #     logger.debug("Background scaling issue: %dx%d on %dx%d wallpaper" % (w, h, width, height))

        fx, fy = -x * output_width / w, -y * output_height / h
        fw, fh = width * output_width / w, height * output_height / h
        # 7. fx, fy, fw, fh are transformed to output coordinates

        # if height > 0 and fh > 0 and abs(fw / fh - width / height) > 0.01:
        #     logger.debug("Background aspect ratio issue: %dx%d on %dx%d wallpaper" % (fw, fh, width, height))

        self.box = (fx, fy, fw, fh)
        self.opacity = opacity

    def set_max(self, wallpaper_size: tuple[int, int], output_size: tuple[float, float]) -> None:
        self.opacity = 1.
        x, y, w, h = 0., 0., float(output_size[0]), float(output_size[1])
        if w/h > wallpaper_size[0]/wallpaper_size[1]:
            new_h = wallpaper_size[1] * w/wallpaper_size[0]
            y -= (new_h - h)/2.
            h = new_h
        else:
            new_w = wallpaper_size[0] * h/wallpaper_size[1]
            x -= (new_w - w)/2.
            w = new_w
        self.box = (x, y, w, h)

    def delta(self, other: BackgroundState) -> float:
        return abs(self.box[0] - other.box[0]) + \
            abs(self.box[1] - other.box[1]) + \
            abs(self.box[2] - other.box[2]) + \
            abs(self.box[3] - other.box[3]) + \
            1000 * abs(self.opacity - other.opacity)

    def approach(self, other: BackgroundState, time_scale: float, dt: float) -> None:
        db = other.box[0] - self.box[0], other.box[1] - self.box[1], other.box[2] - self.box[2], other.box[3] - self.box[3]
        do = other.opacity - self.opacity
        factor = dt / time_scale

        factor = min(1, factor)
        self.opacity += do*factor
        self.box = self.box[0] + db[0] * factor, self.box[1] + db[1] * factor, self.box[2] + db[2] * factor, self.box[3] + db[3] * factor

    def __str__(self) -> str:
        return "<BackgroundState box=%s opacity=%f>" % (str(self.box), self.opacity)


class Background(PyWMBackgroundWidget):
    def __init__(self, wm: Layout, output: PyWMOutput, workspace: Workspace):

        self._output: PyWMOutput = output
        self._workspace: Workspace = workspace

        self._prevent_anim = not conf_anim_default()
        if self._workspace.prevent_anim:
            self._prevent_anim = True

        path = None
        for o in conf_outputs():
            if o['name'] == output.name:
                if 'background' in o:
                    if 'path' in o['background']:
                        path = o['background']['path']
                    if 'anim' in o['background'] and not o['background']['anim']:
                        self._prevent_anim = True

        if path is None:
            path = conf_path_default()

        PyWMBackgroundWidget.__init__(self, wm, output, path)

        self._current_state = BackgroundState(self.wm.state, self.wm.state.get_workspace_state(self._workspace), (self.width, self.height), (self._output.width, self._output.height), self._output.scale)
        self._target_state = BackgroundState(self.wm.state, self.wm.state.get_workspace_state(self._workspace), (self.width, self.height), (self._output.width, self._output.height), self._output.scale)
        self._last_frame: float = time.time()
        self._anim_caught: Optional[float] = None

        if self._prevent_anim:
            self._current_state.set_max((self.width, self.height), (self._output.width, self._output.height))


    def animate(self, old_state: LayoutState, new_state: LayoutState, dt: float) -> None:
        if self._prevent_anim:
            return

        self._anim_caught = time.time() + dt
        self._target_state = BackgroundState(new_state, new_state.get_workspace_state(self._workspace), (self.width, self.height), (self._output.width, self._output.height), self._output.scale)

        self._last_frame = time.time()
        self.damage()

    def process(self) -> PyWMWidgetDownstreamState:
        if not self._prevent_anim:
            # State handling
            t = time.time()

            if self._anim_caught is not None:
                if t > self._anim_caught:
                    self._anim_caught = None
            else:
                target_state = BackgroundState(self.wm.state, self.wm.state.get_workspace_state(self._workspace), (self.width, self.height), (self._output.width, self._output.height), self._output.scale)
                if target_state.delta(self._target_state) > 1:
                    self._target_state = target_state

            if self._current_state.delta(self._target_state) > 1:
                self._current_state.approach(self._target_state, conf_time_scale(), t - self._last_frame)
                self.damage()
            elif self._current_state != self._target_state:
                self._current_state = self._target_state
                self.damage()

            self._last_frame = t

        result = PyWMWidgetDownstreamState()
        result.z_index = -10000
        result.opacity = self._current_state.opacity
        result.box = (self._output.pos[0] + self._current_state.box[0], self._output.pos[1] + self._current_state.box[1], self._current_state.box[2], self._current_state.box[3])
        return result
