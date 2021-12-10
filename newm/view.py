from __future__ import annotations
from typing import Optional, TYPE_CHECKING, cast, TypeVar

import math
import logging
import time

from pywm import PyWMView, PyWMViewDownstreamState, PyWMOutput
from pywm.pywm import PyWMDownstreamState
from pywm.pywm_view import PyWMViewUpstreamState

from .state import ViewState, LayoutState, WorkspaceState
from .interpolation import ViewDownstreamInterpolation
from .animate import Animate
from .overlay import MoveResizeFloatingOverlay
from .config import configured_value
from .util import errorlogged

if TYPE_CHECKING:
    from .layout import Layout, Workspace
else:
    Layout = TypeVar('Layout')


logger = logging.getLogger(__name__)

conf_corner_radius = configured_value('view.corner_radius', 12.5)
conf_padding = configured_value('view.padding', 8)
conf_fullscreen_padding = configured_value('view.fullscreen_padding', 0)
conf_border_ws_switch = configured_value('view.border_ws_switch', 10.)

conf_float_callback = configured_value('view.should_float', lambda view: None)
conf_floating_min_size = configured_value('view.floating_min_size', True)

conf_panel_lock_h = configured_value('panels.lock.h', 0.6)
conf_panel_lock_w = configured_value('panels.lock.w', 0.7)
conf_panel_lock_corner_radius = configured_value('panels.lock.corner_radius', 50)
conf_panel_launcher_h = configured_value('panels.launcher.h', 0.8)
conf_panel_launcher_w = configured_value('panels.launcher.w', 0.8)
conf_panel_launcher_corner_radius = configured_value('panels.launcher.corner_radius', 0)
conf_panel_notifiers_h = configured_value('panels.notifiers.h', 0.3)
conf_panel_notifiers_w = configured_value('panels.notifiers.w', 0.2)

conf_anim_t = configured_value('anim_time', .3)

conf_debug_scaling = configured_value('view.debug_scaling', False)

"""
Wait this long before accepting that view won't accept our requested size
Set high to debug (as this situation should be avoided - possibly there are newm bugs
leading to invalid size requests)

However, in some cases, expiring RESIZE_PATIENCE is a client-side bug (Firefox and pavucontrol e.g.)
After toplevel_configure these windows never repsond with a surface_configure event (before map)

In production .3 or similar should be okay
"""
RESIZE_PATIENCE = .3

class View(PyWMView[Layout], Animate[PyWMViewDownstreamState]):
    def __init__(self, wm: Layout, handle: int):
        PyWMView.__init__(self, wm, handle)
        Animate.__init__(self)

        self._mapped = False
        self._destroyed = False

        # Initial state while waiting for map
        self._initial_time: float = time.time()
        self._initial_kind: int = 0 # 0: panel, 1: layer, 2: float, 3: tiled
        self._initial_state: Optional[PyWMViewDownstreamState] = None

        self.panel: Optional[str] = None
        self.layer_panel: Optional[str] = None

        self._debug_scaling = conf_debug_scaling()

    def __str__(self) -> str:
        if self.up_state is None:
            return "<View %d>" % self._handle

        return "<View %d (%s): %s, %s, %s, %s, xwayland=%s, floating=%s, focused=%s, panel=%s, layer_panel=%s>" % (
            self._handle, ("child(%d)" % self.parent._handle) if self.parent is not None else "root",
             self.title, self.app_id, self.role, self.pid,
             self.is_xwayland, self.up_state.is_floating, self.up_state.is_focused, self.panel, self.layer_panel)

    def is_float(self, state: LayoutState) -> bool:
        if self.is_panel():
            return False

        try:
            s = state.get_view_state(self)
            return not s.is_tiled and not s.is_layer
        except Exception:
            return False

    def is_tiled(self, state: LayoutState) -> bool:
        if self.is_panel():
            return False

        try:
            return state.get_view_state(self).is_tiled
        except Exception:
            return False

    def is_panel(self) -> bool:
        return self.panel is not None

    def _decide_floating(self) -> tuple[bool, Optional[tuple[int, int]], Optional[tuple[float, float]]]:
        size_hint: Optional[tuple[int, int]] = None
        pos_hint: Optional[tuple[float, float]] = None

        floats = self.up_state is not None and self.up_state.is_floating
        try:
            hints = conf_float_callback()(self)
            if hints is not None:
                if isinstance(hints, tuple):
                    if len(hints) >= 1:
                        floats = hints[0]
                    if len(hints) >= 2:
                        size_hint = hints[1]
                    if len(hints) >= 3:
                        pos_hint = hints[2]
                else:
                    floats = hints != False
        except Exception:
            logger.exception("floats callback")

        if (self.up_state is not None and
           self.up_state.size_constraints[0] > 0 and
           self.up_state.size_constraints[2] > 0 and
           self.up_state.size_constraints[0] == self.up_state.size_constraints[1] and
           self.up_state.size_constraints[2] == self.up_state.size_constraints[3]):
            floats = True

        if self.parent is not None:
            floats = True

        return floats, size_hint, pos_hint

    """
    Panel
    """
    def _init_panel(self, up_state: PyWMViewUpstreamState, ws: Workspace) -> PyWMViewDownstreamState:
        return PyWMViewDownstreamState()

    def _reducer_panel(self, up_state: PyWMViewUpstreamState, state: LayoutState, self_state: ViewState, ws: Workspace, ws_state: WorkspaceState) -> PyWMViewDownstreamState:
        result = PyWMViewDownstreamState()

        if self.panel == "notifiers":
            result.z_index = 2000
            result.accepts_input = False
            result.lock_enabled = True

            result.size = (
                int(ws.width * conf_panel_notifiers_w()),
                int(ws.height * conf_panel_notifiers_h()))

            result.box = (
                ws.pos_x + ws.width * (1. - conf_panel_notifiers_w())/2.,
                ws.pos_y + ws.height * (1. - conf_panel_notifiers_h()),
                ws.width * conf_panel_notifiers_w(),
                ws.height * conf_panel_notifiers_h())

        elif self.panel == "launcher":
            result.z_index = 1000
            result.accepts_input = True
            result.corner_radius = conf_panel_launcher_corner_radius()

            result.size = (
                round(ws.width * conf_panel_launcher_w()),
                round(ws.height * conf_panel_launcher_h()))

            result.box = (
                ws.pos_x + (ws.width - result.size[0]) / 2.,
                ws.pos_y + (ws.height - result.size[1]) / 2. + (1. - state.launcher_perc) * ws.height,
                result.size[0],
                result.size[1])

        elif self.panel == "lock":
            result.z_index = 10000
            result.accepts_input = True
            result.corner_radius = conf_panel_lock_corner_radius()
            result.lock_enabled = True

            result.size = (
                round(ws.width * conf_panel_lock_w()),
                round(ws.height * conf_panel_lock_h()))

            result.box = (
                ws.pos_x + (ws.width - result.size[0]) / 2.,
                ws.pos_y + (ws.height - result.size[1]) / 2. + (1. - state.lock_perc) * ws.height,
                result.size[0],
                result.size[1])

        return result

    def _show_panel(self, ws: Workspace, state: LayoutState, ws_state:WorkspaceState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
        logger.info("Show - panel: %s %s", self.panel, self)
        self.damage()

        # Place dummy ViewState
        ws_state1 = ws_state.with_view_state(self, is_tiled=False, is_layer=True)
        state1 = state.setting_workspace_state(ws, ws_state1)
        return state1, None

    """
    Layer
    """
    def _layer_placement(self, output: PyWMOutput, size_constraints: list[int], size: Optional[tuple[int, int]]=None) -> tuple[tuple[int, int], tuple[int, int, int, int]]:
        anchor = size_constraints[0]
        width = size_constraints[1]
        height = size_constraints[2]
        margin = size_constraints[5:]

        if size is not None and size[0] > 0 and size[1] > 0:
            width, height = size

        x = 0
        y = 0

        anchored_top = bool(anchor & 1)
        anchored_bottom = bool(anchor & 2)
        anchored_left = bool(anchor & 4)
        anchored_right = bool(anchor & 8)

        if width == 0:
            if not anchored_left or not anchored_right:
                logger.warn("Layer shell protocol error")
            width = output.width - margin[0] - margin[2]
        if height == 0:
            if not anchored_top or not anchored_bottom:
                logger.warn("Layer shell protocol error")
            height = output.height - margin[1] - margin[3]

        if anchored_right:
            x = output.width - margin[2] - width
        elif anchored_left:
            x = margin[0]
        else:
            x = (output.width - width) // 2

        if anchored_bottom:
            y = output.height - margin[3] - height
        elif anchored_top:
            y = margin[1]
        else:
            y = (output.height - height) // 2


        target_width, target_height = size_constraints[1:3]

        if target_width == 0:
            target_width = width
        if target_height == 0:
            target_height = height

        if anchored_top and ((anchored_left and anchored_right) or target_width == output.width) and not anchored_bottom and target_height < 0.2*output.height:
            self.layer_panel = "top_bar"
        elif anchored_bottom and ((anchored_left and anchored_right) or target_width == output.width) and not anchored_top and target_height < 0.2*output.height:
            self.layer_panel = "bottom_bar"

        return (target_width, target_height), (x + output.pos[0], y + output.pos[1], width, height)


    def _init_layer(self, up_state: PyWMViewUpstreamState, ws: Workspace) -> PyWMViewDownstreamState:
        result = PyWMViewDownstreamState()

        result.fixed_output = up_state.fixed_output if (up_state.fixed_output is not None) else ws.outputs[0]
        result.size, _ = self._layer_placement(result.fixed_output, up_state.size_constraints)
        return result

    def _reducer_layer(self, up_state: PyWMViewUpstreamState, state: LayoutState, self_state: ViewState, ws: Workspace, ws_state: WorkspaceState) -> PyWMViewDownstreamState:
        result = PyWMViewDownstreamState()
        result.floating = True
        result.accepts_input = True
        result.corner_radius = 0
        result.fixed_output = up_state.fixed_output

        # z_index based on layer
        layer = up_state.size_constraints[4]
        if layer == 0:
            result.z_index = -2000
        elif layer == 1:
            result.z_index = -1000
        elif layer == 2:
            result.z_index = 1000
        elif layer == 3:
            result.z_index = 2000

        # Keep focused view on top
        if self.is_focused():
            result.z_index += 1

        if result.fixed_output is None:
            result.fixed_output = self.wm.layout[0]
            logger.debug("Manually assigning fixed output: %s" % self.wm.layout[0])

        result.size, result.box = self._layer_placement(result.fixed_output, up_state.size_constraints, up_state.size)

        if self.layer_panel == "top_bar":
            x, y, w, h = 0., 0., 0., 0. # mypy
            x, y, w, h = result.box
            y -= h * 1.2 * (1. - ws_state.top_bar_dy)
            result.box = x, y, w, h
        elif self.layer_panel == "bottom_bar":
            x, y, w, h = 0., 0., 0., 0. # mypy
            x, y, w, h = result.box
            y += h * 1.2 * (1. - ws_state.bottom_bar_dy)
            result.box = x, y, w, h

        if self_state.layer_initial:
            result.box = result.box[0] + .5*result.box[2], result.box[1] + .5*result.box[3], 0, 0

        result.mask = (-100000, -100000, result.size[0] + 200000, result.size[1] + 200000)

        result.opacity = 1.0 if (result.lock_enabled and not state.final) else state.background_opacity
        result.workspace = None

        return result

    def _show_layer(self, ws: Workspace, state: LayoutState, ws_state: WorkspaceState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
        logger.info("Show - layer: %s", self)

        if self.layer_panel is None:
            ws_state1 = ws_state.copy().with_view_state(self, is_tiled=False, is_layer=True, layer_initial=True)
            ws_state2 = ws_state.copy().with_view_state(self, is_tiled=False, is_layer=True)

            self.focus()
            return state.setting_workspace_state(ws, ws_state1), state.setting_workspace_state(ws, ws_state2)
        else:
            ws_state1 = ws_state.copy().with_view_state(self, is_tiled=False, is_layer=True)
            return state.setting_workspace_state(ws, ws_state1), None

    """
    Floating
    """
    def _init_floating(self, up_state: PyWMViewUpstreamState, ws: Workspace, size_hint: Optional[tuple[int, int]]=None, pos_hint: Optional[tuple[float, float]]=None) -> PyWMViewDownstreamState:
        """
        Set floating attributes on init if it is clear the window will float
        """
        result = PyWMViewDownstreamState()

        width, height = up_state.size
        if size_hint is not None:
            width, height = size_hint
        elif conf_floating_min_size():
            if up_state.size_constraints[0] > 0 and up_state.size_constraints[2] > 0:
                width, height = up_state.size_constraints[0], up_state.size_constraints[2]

        min_w, max_w, min_h, max_h = up_state.size_constraints
        if max_w <= 0:
            max_w = width
        if max_h <= 0:
            max_h = height
        width = max(min_w, min(max_w, width))
        height = max(min_h, min(max_h, height))

        result.floating = True
        result.size = (width, height)

        logger.debug("Floating size decision: %dx%d (%s) --> %dx%d" % (*up_state.size,
                                                                        up_state.size_constraints, width, height))

        return result


    def _reducer_floating(self, up_state: PyWMViewUpstreamState, state: LayoutState, self_state: ViewState, ws: Workspace, ws_state: WorkspaceState) -> PyWMViewDownstreamState:
        result = PyWMViewDownstreamState()
        result.floating = True
        result.accepts_input = True
        result.corner_radius = conf_corner_radius() if self.parent is None else 0

        result.corner_radius /= max(1, ws_state.size / 2.)

        # z_index based on hierarchy
        depth = 0
        p = self.parent
        while p is not None:
            depth += 1
            p = p.parent

        result.z_index = depth + 2

        # Keep focused view on top
        if self.is_focused():
            result.z_index += 1

        # Handle client size
        result.size = self_state.float_size if self_state.float_size[0] > 0 else (-1, -1)
        width, height = up_state.size

        # For animation purposes
        if self_state.float_size == (0, 0):
            width, height = 0, 0

        # Handle box
        size = ws_state.size_origin if ws_state.size_origin is not None else ws_state.size
        width = round(width * size / ws_state.size)
        height = round(height * size / ws_state.size)

        i, j = self_state.float_pos

        x = i - ws_state.i
        y = j - ws_state.j

        x *= ws.width / ws_state.size
        y *= ws.height / ws_state.size
        result.box = (x, y, width, height)

        ox, oy = up_state.offset
        ox = abs(ox)
        oy = abs(oy)
        result.mask = (-10*ox, -10*oy, width + 20*ox, height + 20*oy)

        result.opacity = 1.0 if (result.lock_enabled and not state.final) else state.background_opacity
        result.box = (result.box[0] + ws.pos_x, result.box[1] + ws.pos_y, result.box[2], result.box[3])

        # Workspaces don't really matter for floating windows, just leave them attached to initial workspace
        result.workspace = None

        return result


    def _show_floating(self, ws: Workspace, state: LayoutState, ws_state: WorkspaceState, size_hint: Optional[tuple[int, int]], pos_hint: Optional[tuple[float, float]]) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
        logger.debug("Show - floating: %s" % self)

        # mypy
        if self._initial_state is None:
            return None, None

        reference_state = state
        if state.all_in_overview():
            reference_state = state.with_overview_set(False)
        elif ws_state.is_in_overview():
            reference_state = state.with_overview_set(False, only_workspace=ws)
        else:
            reference_state = state.copy()
        reference_ws_state = reference_state.get_workspace_state(ws)


        width, height = self._initial_state.size
        w, h = width, height

        if pos_hint is not None:
            ci = reference_ws_state.i + pos_hint[0] * reference_ws_state.size
            cj = reference_ws_state.j + pos_hint[1] * reference_ws_state.size
            logger.debug("Respecting position hint %f %f -> %f %f" % (*pos_hint, ci, cj))

        elif self.parent is not None:
            try:
                p_state = reference_state.get_view_state(cast(View, self.parent))
                if p_state.is_tiled:
                    ci = p_state.i + p_state.w / 2.
                    cj = p_state.j + p_state.h / 2.
                else:
                    ci = p_state.float_pos[0] + p_state.float_size[0] * reference_ws_state.size / ws.width / 2.
                    cj = p_state.float_pos[1] + p_state.float_size[1] * reference_ws_state.size / ws.width / 2.
            except:
                logger.warn("Unexpected: Could not access parent %s state" % self.parent)
        else:
            ci = reference_ws_state.i + reference_ws_state.size / 2.
            cj = reference_ws_state.j + reference_ws_state.size / 2.


        wt, ht = w / ws.width * reference_ws_state.size, h / ws.height * reference_ws_state.size
        i = ci - wt / 2.
        j = cj - ht / 2.

        ws_state1 = ws_state.with_view_state(
            self,
            is_tiled=False,
            float_pos=(ci, cj),
            float_size=(0, 0),
            stack_idx=self._handle,
        )

        ws_state2 = reference_ws_state.with_view_state(
            self,
            is_tiled=False,
            float_pos=(i, j),
            float_size=(w, h),
            stack_idx=self._handle,
        )

        self.focus()
        return state.setting_workspace_state(ws, ws_state1), reference_state.setting_workspace_state(ws, ws_state2)


    """
    Tiled
    """
    def _init_tiled(self, up_state: PyWMViewUpstreamState, ws: Workspace) -> PyWMViewDownstreamState:
        """
        Make a best-guess assumption w=h=1 and workspace size unchanged to ask the view to open with correct size
        Note that we can't be sure the view is going to be tiled at this stage - views do change min / max sizes later on
        which means they might be detected as floating in on_map
        """
        ws_state = self.wm.state.get_workspace_state(ws)
        result = self._reducer_tiled(up_state, self.wm.state, ViewState(w=1, h=1), ws, ws_state)
        result.box = (0, 0, 0, 0)
        result.floating = None
        return result


    def _reducer_tiled(self, up_state: PyWMViewUpstreamState, state: LayoutState, self_state: ViewState, ws: Workspace, ws_state: WorkspaceState) -> PyWMViewDownstreamState:
        result = PyWMViewDownstreamState()
        result.floating = False
        result.accepts_input = True
        result.corner_radius = conf_corner_radius()

        if ws_state.is_fullscreen() and conf_fullscreen_padding() == 0:
            result.corner_radius = 0

        """
        z_index based on hierarchy
        """
        depth = 0
        p = self.parent
        while p is not None:
            depth += 1
            p = p.parent

        result.z_index = depth

        """
        Keep focused view on top
        """
        if self.is_focused():
            result.z_index += 1

        """
        Handle box
        """
        i = self_state.i
        j = self_state.j
        w = self_state.w
        h = self_state.h

        _, stack_idx, stack_len = self_state.stack_data
        if stack_len > 1:
            i += 0.05 * stack_idx / (stack_len - 1)
            j += 0.05 * ws.width / ws.height * stack_idx / (stack_len - 1)
            w -= 0.05
            h -= 0.05 * ws.width / ws.height

        x = i - ws_state.i
        y = j - ws_state.j

        x *= ws.width / ws_state.size
        y *= ws.height / ws_state.size
        w *= ws.width / ws_state.size
        h *= ws.height / ws_state.size

        result.corner_radius /= max(1, ws_state.size / 2.)

        padding = float(conf_fullscreen_padding() if ws_state.is_fullscreen() else conf_padding())
        padding_scaled = padding / max(1, ws_state.size / 2.)

        padding_for_size = padding_scaled
        if ws_state.size_origin is not None:
            padding_for_size = padding / max(1, ws_state.size_origin / 2.)

        if w != 0 and h != 0:
            x += padding_scaled
            y += padding_scaled
            w -= 2*padding_scaled
            h -= 2*padding_scaled

        """
        An attempt to reduce the effect of dreadful CSD
        As always Chrome is ahead in this regard, rendering completely unwanted shadows
        --> If up_state.offset indicates weird CSD stuff going on, just fix the tile using masks
        """
        mask_origin = (0., 0.)
        if up_state.size[0] > 0 and up_state.size[1] > 0:
            ox = up_state.offset[0] / up_state.size[0] * w
            oy = up_state.offset[1] / up_state.size[1] * h
            x -= ox
            y -= oy
            mask_origin = ox, oy

        """
        Handle client size
        """
        if self_state.scale_origin is not None:
            w_for_size, h_for_size = self_state.scale_origin
        else:
            w_for_size, h_for_size = self_state.w, self_state.h

        size = ws_state.size_origin if ws_state.size_origin is not None else ws_state.size

        if stack_len > 1:
            w_for_size -= 0.05
            h_for_size -= 0.05 * ws.width / ws.height

        w_for_size *= ws.width / size
        h_for_size *= ws.height / size

        w_for_size -= 2*padding_for_size
        h_for_size -= 2*padding_for_size

        width = round(w_for_size)
        height = round(h_for_size)

        result.size = (width, height)

        """
        Override: Keep aspect-ratio of windows
        """
        min_w, max_w, min_h, max_h = up_state.size_constraints

        if width < min_w and min_w > 0:
            width = min_w
        if width > max_w and max_w > 0:
            width = max_w
        if height < min_h and min_h > 0:
            height = min_h
        if height > max_h and max_h > 0:
            width = min_w

        old_ar = result.size[1] / result.size[0] if result.size[0] > 0 else 1.
        new_ar = height / width if width > 0 else 1.

        if abs(old_ar - new_ar) > 0.001:
            if new_ar < old_ar:
                # new width is larger - would appear scaled up vertically
                h *= new_ar / old_ar
            else:
                # new width is smaller - would appear scaled up horizontally
                w *= old_ar / new_ar

        result.size = (width, height)
        result.box = (x, y, w, h)

        result.mask = (mask_origin[0], mask_origin[1], w, h)

        result.opacity = 1.0 if (result.lock_enabled and not state.final) else state.background_opacity
        result.box = (result.box[0] + ws.pos_x, result.box[1] + ws.pos_y, result.box[2], result.box[3])

        if self_state.move_origin is not None and self_state.scale_origin is None:
            # No fixed output during a move
            result.workspace = None
        else:
            result.workspace = (ws.pos_x, ws.pos_y, ws.width, ws.height)

        return result


    def _show_tiled(self, ws: Workspace, state: LayoutState, ws_state:WorkspaceState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
        logger.debug("Show - tiled: %s" % self)
        min_w, _, min_h, _ = self.up_state.size_constraints if self.up_state is not None else (0., 0., 0., 0.)
        size = ws_state.size
        if ws_state.size_origin is not None:
            size = ws_state.size_origin
        min_w *= size / ws.width
        min_h *= size / ws.height

        w = max(math.ceil(min_w), 1)
        h = max(math.ceil(min_h), 1)

        reference_state = state
        if state.all_in_overview():
            reference_state = state.with_overview_set(False)
        elif ws_state.is_in_overview():
            reference_state = state.with_overview_set(False, only_workspace=ws)
        else:
            reference_state = state.copy()
        reference_ws_state = reference_state.get_workspace_state(ws)

        i: float = 0.
        j: float = 0.
        i, j = self.wm.place_initial(ws, reference_ws_state, w, h)

        second_state = (i, j, w, h)

        i, j, w, h = second_state
        i1, j1, w1, h1 = second_state

        i += .5*w
        j += .5*h
        w = 0
        h = 0

        ws_state1 = ws_state.with_view_state(
            self,
            is_tiled=True, i=i, j=j, w=w, h=h,
            scale_origin=(w1, h1), move_origin=(i1, j1, ws),
            stack_idx=self._handle,
        )

        ws_state2 = reference_ws_state.with_view_state(
            self,
            is_tiled=True, i=i1, j=j1, w=w1, h=h1,
            scale_origin=None, move_origin=None,
            stack_idx=self._handle,
        ).focusing_view(self)

        self.focus()
        return state.setting_workspace_state(ws, ws_state1), reference_state.setting_workspace_state(ws, ws_state2)

    """
    Init and map
    """
    def init(self) -> PyWMViewDownstreamState:
        logger.info("Init: %s", self)

        # mypy
        if self.up_state is None:
            return PyWMViewDownstreamState()

        ws = self.wm.get_active_workspace()
        if self.up_state is not None and (output := self.up_state.fixed_output) is not None:
            wss = [w for w in self.wm.workspaces if output in w.outputs]
            if len(wss) != 1:
                logger.warn("Unexpected: Could not find output %s in workspaces" % output)
            else:
                ws = wss[0]

        if self.pid is not None:
            self.panel = self.wm.panel_launcher.get_panel_for_pid(self.pid)

        if self.panel is not None:
            self._initial_kind = 0
            self._initial_state = self._init_panel(self.up_state, ws)

        elif self.role == "layer":
            self._initial_kind = 1
            self._initial_state = self._init_layer(self.up_state, ws)

        else:
            floats, size_hint, pos_hint = self._decide_floating()

            if floats:
                self._initial_kind = 2
                self._initial_state = self._init_floating(self.up_state, ws, size_hint=size_hint, pos_hint=pos_hint)

            else:
                self._initial_kind = 3
                self._initial_state = self._init_tiled(self.up_state, ws)

        self.damage()
        return self._initial_state

    def show(self, state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
        logger.info("Show: %s", self)

        if self._destroyed:
            logger.debug("Preventing show of destroyed view")
            return None, None

        if self._mapped:
            logger.debug("Duplicate show")
            return None, None

        ws = self.wm.get_active_workspace()
        if self.up_state is not None and (output := self.up_state.fixed_output) is not None:
            wss = [w for w in self.wm.workspaces if output in w.outputs]
            if len(wss) != 1:
                logger.warn("Unexpected: Could not find output %s in workspaces" % output)
            else:
                ws = wss[0]

        ws_state = state.get_workspace_state(ws)

        if self._initial_kind == 0:
            result = self._show_panel(ws, state, ws_state)

        elif self._initial_kind == 1:
            result = self._show_layer(ws, state, ws_state)

        else:
            _, size_hint, pos_hint = self._decide_floating()

            if self._initial_kind == 2:
                result = self._show_floating(ws, state, ws_state, size_hint=size_hint, pos_hint=pos_hint)
            else:
                result = self._show_tiled(ws, state, ws_state)

        if result != (None, None):
            self._mapped = True

        return result


    def process(self, up_state: PyWMViewUpstreamState) -> PyWMViewDownstreamState:
        if self._mapped:
            return self._process(self.reducer(up_state, self.wm.state))

        self.damage()
        self.init()

        # mypy
        if self._initial_state is None:
            return PyWMViewDownstreamState()

        state, kind = self._initial_state, self._initial_kind
        if kind != self._initial_kind:
            logger.debug("View %s changed kind: %d -> %d", kind, self._initial_kind)
            return self._initial_state

        if up_state.size != self._initial_state.size and self._initial_state.size[0] > 0 and self._initial_state.size[1] > 0 and up_state.size[0] > 0 and up_state.size[1] > 0:
            if time.time() - self._initial_time < RESIZE_PATIENCE:
                self.force_size()
                return self._initial_state
            else:
                logger.info("Size negotiation failed - Allowing view custom size %dx%d (instead of %dx%d)" % (*up_state.size,
                                                                                                              *self._initial_state.size))

        if up_state.is_mapped:
            self.wm.animate_to(self.show, conf_anim_t(), None)
        return self._initial_state


    """
    Animation logic
    """
    def reducer(self, up_state: PyWMViewUpstreamState, state: LayoutState) -> PyWMViewDownstreamState:
        try:
            self_state, ws_state, ws_handle = state.find_view(self)
            ws = [w for w in self.wm.workspaces if w._handle == ws_handle][0]
        except Exception:
            """
            This is perfectly valid: One animation is queued, after which the show animation of
            this view is queued. Upon start of the first animation we're here.
            """
            if self._initial_state is not None:
                return self._initial_state

            """
            This however shouldn't happen
            """
            logger.warn("Missing state: %s" % self)
            return PyWMViewDownstreamState(up_state=up_state)

        if self.panel is not None:
            return self._reducer_panel(up_state, state, self_state, ws, ws_state)
        elif self_state.is_tiled:
            return self._reducer_tiled(up_state, state, self_state, ws, ws_state)
        elif self_state.is_layer:
            return self._reducer_layer(up_state, state, self_state, ws, ws_state)
        else:
            return self._reducer_floating(up_state, state, self_state, ws, ws_state)


    def animate(self, old_state: LayoutState, new_state: LayoutState, dt: float) -> None:
        if self.up_state is None:
            return

        cur = self.reducer(self.up_state, old_state)
        nxt = self.reducer(self.up_state, new_state)

        self._animate(ViewDownstreamInterpolation(self.wm, cur, nxt), dt)

    """
    Public API
    """
    def is_focused(self) -> bool:
        return self.up_state is not None and self.up_state.is_focused

    def destroy(self) -> None:
        self._destroyed = True
        self.wm.destroy_view(self)

    def toggle_floating(self, state: ViewState, ws: Workspace, ws_state: WorkspaceState) -> tuple[ViewState, ViewState]:
        padding = conf_padding() if not ws_state.is_fullscreen() else 0
        if state.is_tiled:
            float_size = self.up_state.size if self.up_state is not None else (100, 100)
            float_pos = state.i + 0.1, state.j - 0.1
            return state, state.copy(is_tiled=False, float_size=float_size, float_pos=float_pos)

        else:
            w = max(1, round((state.float_size[0] + 2*padding) / ws.width * ws_state.size))
            h = max(1, round((state.float_size[1] + 2*padding) / ws.height * ws_state.size))
            i = round(state.float_pos[0])
            j = round(state.float_pos[1])
            return state, state.copy(is_tiled=True, i=i, j=j, w=w, h=h)

        return state.copy(is_tiled=not self.is_floating, i=i, j=j, w=w, h=h)


    def transform_to_closest_ws(self, ws: Workspace, i0: float, j0: float, w0: float, h0: float) -> tuple[Workspace, float, float, float, float]:
        if self.panel is not None or self.up_state is None:
            return ws, i0, j0, w0, h0

        ws_state = self.wm.state.get_workspace_state(ws)
        border_ws_switch = conf_border_ws_switch()
        if self.is_float(self.wm.state):
            down = self._reducer_floating(self.up_state, self.wm.state, ViewState(is_tiled=False, float_pos=(i0, j0), float_size=(w0, h0)), ws, ws_state)

            x, y, w, h = down.box

            cx = x + .5*w
            cy = y + .5*h

            size = ws_state.size_origin if ws_state.size_origin is not None else ws_state.size

            if ws.pos_x - border_ws_switch <= cx <= ws.pos_x + ws.width + border_ws_switch and ws.pos_y - border_ws_switch <= cy <= ws.pos_y + ws.height + border_ws_switch:
                return ws, i0, j0, w0, h0

            for wsp in self.wm.workspaces:
                if wsp.pos_x < cx < wsp.pos_x + wsp.width and wsp.pos_y < cy < wsp.pos_y + wsp.height:
                    statep = self.wm.state.copy()
                    statep.move_view_state(self, ws, wsp)
                    statep.update_view_state(self, float_pos=(0, 0))

                    view_state, wsp_state, _ = statep.find_view(self)
                    down_transformed = self._reducer_floating(self.up_state, statep, view_state, wsp, wsp_state)

                    xp, yp, widthp, heightp = down_transformed.box
                    cxp = xp + .5 * widthp
                    cyp = yp + .5 * heightp

                    ip = (cx - cxp) * wsp_state.size / wsp.width
                    jp = (cy - cyp) * wsp_state.size / wsp.height

                    return wsp, ip, jp, w0, h0

        else:
            down = self._reducer_tiled(self.up_state, self.wm.state, ViewState(i=i0, j=j0, w=w0, h=h0), ws, ws_state)

            x, y, w, h = down.box

            cx = x + .5*w
            cy = y + .5*h

            if ws.pos_x - border_ws_switch <= cx <= ws.pos_x + ws.width + border_ws_switch and ws.pos_y - border_ws_switch <= cy <= ws.pos_y + ws.height + border_ws_switch:
                return ws, i0, j0, w0, h0

            for wsp in self.wm.workspaces:
                if wsp.pos_x < cx < wsp.pos_x + wsp.width and wsp.pos_y < cy < wsp.pos_y + wsp.height:
                    wsp_state = self.wm.state.get_workspace_state(wsp)

                    # Keep original size when moving to an overview state or leaving one
                    if wsp_state.is_in_overview() or ws_state.is_in_overview():
                        wp = w0
                        hp = h0
                    else:
                        wp = max(1, min(wsp_state.size, round(w * wsp_state.size / wsp.width)))
                        hp = max(1, min(wsp_state.size, round(h * wsp_state.size / wsp.height)))

                    ip, jp = 0., 0.
                    statep = self.wm.state.copy()
                    statep.move_view_state(self, ws, wsp)
                    statep.update_view_state(self, i=ip, j=jp, w=wp, h=hp)
                    for _ in range(3):

                        statep.update_view_state(self, i=ip, j=jp)

                        view_state, wsp_state, _ = statep.find_view(self)
                        down_transformed = self._reducer_tiled(self.up_state, statep, view_state, wsp, wsp_state)

                        xp, yp, widthp, heightp = down_transformed.box
                        cxp = xp + .5 * widthp
                        cyp = yp + .5 * heightp

                        ip += (cx - cxp) * wsp_state.size / wsp.width
                        jp += (cy - cyp) * wsp_state.size / wsp.height

                    return wsp, ip, jp, wp, hp

        logger.debug("View outside of workspaces - defaulting")
        return ws, i0, j0, w0, h0

    """
    Callbacks
    """
    def on_event(self, event: str) -> None:
        if event == "request_move":
            if self.up_state is not None and self.up_state.is_floating:
                self.wm.enter_overlay(
                    MoveResizeFloatingOverlay(self.wm, self))
        elif event == "request_fullscreen":
            logger.debug("Client requested fullscreen - following")
            if self.is_focused():
                self.wm.toggle_fullscreen(True)
            self.set_fullscreen(True)
        elif event == "request_nofullscreen":
            logger.debug("Client requests to leave fullscreen - following")
            if self.is_focused():
                self.wm.toggle_fullscreen(False)
            self.set_fullscreen(False)

    def on_resized(self, width: int, height: int, client_leading: bool) -> None:
        if client_leading and self.up_state is not None and self.up_state.is_floating:
            try:
                self_state = self.wm.state.get_view_state(self)
                if self_state.scale_origin is None:
                    self.wm.state.update_view_state(self, float_size=(width, height))
                    self.damage()
            except:
                # OK, on_resized is called before map
                pass

    def on_focus_change(self) -> None:
        if self.is_focused():
            self.wm.focus_hint(self)
