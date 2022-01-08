from __future__ import annotations
from typing import Optional, Callable, TYPE_CHECKING, TypeVar, Union, Any, cast

import time
import math
import logging
import subprocess
import os
from itertools import product
from threading import Thread

from pywm import (
    PyWM,
    PyWMOutput,
    PyWMDownstreamState,
    PYWM_MOD_CTRL,
    PYWM_PRESSED,
    PYWM_MOD_ALT,
    PYWM_MOD_LOGO
)
from pywm.touchpad import (
    TwoFingerSwipePinchGesture,
    HigherSwipeGesture,
    SingleFingerMoveGesture
)
from pywm.touchpad.gestures import Gesture

from .state import LayoutState, WorkspaceState
from .interpolation import LayoutDownstreamInterpolation
from .animate import Animate
from .view import View
from .config import configured_value, load_config, print_config

from .key_processor import KeyProcessor
from .panel_endpoint import PanelEndpoint
from .panel_launcher import PanelsLauncher
from .auth_backend import AuthBackend

from .widget import (
    TopBar,
    BottomBar,
    Background,
    Corner,
    FocusBorders
)
from .overlay import (
    Overlay,
    MoveResizeOverlay,
    MoveResizeFloatingOverlay,
    SwipeOverlay,
    SwipeToZoomOverlay,
    LauncherOverlay,
)

logger = logging.getLogger(__name__)

conf_mod = configured_value('mod', PYWM_MOD_LOGO)
conf_pywm = configured_value('pywm', cast(dict[str, Any], {}))

conf_outputs = configured_value('outputs', cast(list[dict[str, Any]], []))

conf_send_fullscreen_to_views = configured_value('view.send_fullscreen', True)

if TYPE_CHECKING:
    TKeyBindings = Callable[[Layout], list[tuple[str, Callable[[], None]]]]
else:
    TKeyBindings = TypeVar('TKeyBindings')

conf_key_bindings = configured_value('key_bindings', cast(TKeyBindings, lambda layout: []))

conf_lp_freq = configured_value('gestures.lp_freq', 60.)
conf_lp_inertia = configured_value('gestures.lp_inertia', .8)
conf_two_finger_min_dist = configured_value('gestures.two_finger_min_dist', .1)
conf_validate_threshold = configured_value('gestures.validate_threshold', .02)

conf_anim_t = configured_value('anim_time', .3)
conf_blend_t = configured_value('blend_time', 1.)

conf_idle_times = configured_value('energy.idle_times', [120, 300, 600])
conf_suspend_command = configured_value('energy.suspend_command', "systemctl suspend")
"""
code == 'lock': Called on lock - idea is to dim the screen now
code == 'idle': Called after idle_times[0] has passed
code == 'idle-lock': Called after idle_times[1] has passed - the screen is locked additionally
code == 'idle-suspend': Called after idle_times[2] has passed - the computer is suspended additionally
code == 'active': Called on activity after idle
"""
conf_idle_callback = configured_value('energy.idle_callback', lambda code: None)

conf_on_startup = configured_value('on_startup', lambda: None)
conf_on_reconfigure = configured_value('on_reconfigure', lambda: None)
conf_lock_on_wakeup = configured_value('lock_on_wakeup', True)

conf_bar_enabled = configured_value('bar.enabled', True)

def _score(i1: float, j1: float, w1: float, h1: float,
           im: int, jm: int,
           i2: float, j2: float, w2: float, h2: float) -> float:

    if (i1, j1, w1, h1) == (i2, j2, w2, h2):
        return 1000

    if im < 0:
        im *= -1
        i1 *= -1
        i2 *= -1
        i1 -= w1
        i2 -= w2
    if jm < 0:
        jm *= -1
        j1 *= -1
        j2 *= -1
        j1 -= h1
        j2 -= h2

    if jm == 1 and im == 0:
        im, jm = jm, im
        i1, j1, w1, h1 = j1, i1, h1, w1
        i2, j2, w2, h2 = j2, i2, h2, w2

    """
    At this point: im == 1, jm == 0
    """
    d_i = i2 - (i1 + w1)
    if d_i < 0:
        return 1000

    d_j = 0.
    if j2 >= j1 + h1:
        d_j = j2 - (j1 + h1)
    elif j1 >= j2 + h2:
        d_j = j1 - (j2 + h2)
    else:
        d_j = -1

    return d_i + d_j


class Animation:
    def __init__(self,
                 layout: Layout,
                 reducer: Callable[[LayoutState], tuple[Optional[LayoutState], Optional[LayoutState]]],
                 duration: float, then: Optional[Callable[..., None]], overlay_safe: bool=False) -> None:
        super().__init__()
        self.layout = layout

        """
        (current state) -> (animation initial state (possibly None), animation final state)
        """
        self.reducer = reducer

        self._initial_state: Optional[LayoutState] = None
        self._final_state: Optional[LayoutState] = None
        self._started: Optional[float] = None

        # Prevent devision by zero
        self.duration = max(.1, duration)

        self.then = then
        self.overlay_safe = overlay_safe

    def check_finished(self) -> bool:
        if self._started is not None and self._final_state is None:
            return True

        if self._started is not None and time.time() > self._started + self.duration:
            if self._final_state is not None:
                self.layout.update(self._final_state)
            if callable(self.then):
                self.then()
            return True

        return False

    def start(self) -> None:
        try:
            self._initial_state, self._final_state = self.reducer(self.layout.state)
        except:
            logger.exception("During animation reducer")
            self._initial_state, self._final_state = None, None

        if self._initial_state is not None:
            self.layout.update(self._initial_state)

        self._started = time.time()
        if self._final_state is not None:
            # Enforce constraints on final state
            self._final_state.constrain()
            self._final_state.validate_fullscreen()
            self._final_state.validate_stack_indices()

            self.layout._animate_to(self._final_state, self.duration)
        else:
            logger.debug("Animation decided not to take place anymore")

    def __str__(self) -> str:
        return "%s -> %s (%f%s)" % (self._initial_state, self._final_state, self.duration, ", then" if self.then is not None else "")


class LayoutThread(Thread):
    def __init__(self, layout: Layout) -> None:
        super().__init__()
        self.layout = layout

        """
        Overlay or Animation
        """
        self._pending: list[Any] = []
        self._current_ovr: Optional[Overlay] = None
        self._current_anim: Optional[Animation] = None

        self._running = True

    def stop(self) -> None:
        self._running = False

    def push(self, nxt: Union[Overlay, Animation]) -> None:
        if isinstance(nxt, Overlay):
            if self._current_ovr is not None or len([x for x in self._pending if isinstance(x, Overlay)]) > 0:
                logger.debug("Rejecting queued overlay")
                return
            else:
                logger.debug("Queuing overlay")
                self._pending += [nxt]
        else:
            if nxt.overlay_safe:
                logger.debug("Overlay-safe animation not queued")
                self._pending = [nxt] + self._pending
            else:
                logger.debug("Queuing animation")
                self._pending += [nxt]

    def on_overlay_destroyed(self) -> None:
        logger.debug("Thread: Finishing overlay...")
        self._current_ovr = None

    def run(self) -> None:
        while self._running:
            try:
                if len(self._pending) > 0:
                    if isinstance(self._pending[0], Overlay):
                        if self._current_anim is None and self._current_ovr is None:
                            logger.debug("Thread: Starting overlay...")
                            self._current_ovr = self._pending.pop(0)
                            self.layout.start_overlay(self._current_ovr)
                    else:
                        if self._current_anim is None and (self._current_ovr is None or self._pending[0].overlay_safe):
                            logger.debug("Thread: Starting animation...")
                            self._current_anim = self._pending.pop(0)
                            self._current_anim.start()

                if self._current_anim is not None:
                    if self._current_anim.check_finished():
                        logger.debug("Thread: Finishing animation...")
                        self._current_anim = None

            except Exception:
                logger.exception("Unexpected during LayoutThread")

            time.sleep(1. / 120.)


class Workspace:
    def __init__(self, output: PyWMOutput, pos_x: int, pos_y: int, width: int, height: int, prevent_anim: bool=False) -> None:
        self._handle = -1
        self.outputs = [output]

        self.pos_x = pos_x
        self.pos_y = pos_y
        self.width = width
        self.height = height

        self.prevent_anim = prevent_anim

        # Hint at view._handle to focus when switching to this workspace (not guaranteed to exist anymore)
        self.focus_view_hint: Optional[int] = None

    def swallow(self, other: Workspace) -> bool:
        if self.pos_x + self.width <= other.pos_x:
            return False
        if self.pos_y + self.height <= other.pos_y:
            return False
        if self.pos_x >= other.pos_x + other.width:
            return False
        if self.pos_y >= other.pos_y + other.height:
            return False

        pos_x = min(self.pos_x, other.pos_x)
        pos_y = min(self.pos_y, other.pos_y)
        width = max(self.pos_x + self.width, other.pos_x + other.width) - pos_x
        height = max(self.pos_y + self.height, other.pos_y + other.height) - pos_y
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.width = width
        self.height = height
        self.outputs += other.outputs
        self.prevent_anim |= other.prevent_anim

        return True

    def score(self, other: Workspace) -> float:
        x, y, w, h = self.pos_x, self.pos_y, self.width, self.height
        if other.pos_x > x:
            w -= (other.pos_x - x)
            x += (other.pos_x - x)
        if other.pos_y > y:
            h -= (other.pos_y - y)
            y += (other.pos_y - y)
        if x + w > other.pos_x + other.width:
            w -= (x + w - other.pos_x - other.width)
        if y + h > other.pos_y + other.height:
            h -= (y + h - other.pos_y - other.height)

        if w <= 0 or h <= 0:
            return 0

        return w*h / (self.width * self.height)

    def __str__(self) -> str:
        return "Workspace[%d] at %d, %d --> %d, %d" % (
            self._handle,
            self.pos_x,
            self.pos_y,
            self.width,
            self.height,
        )


class Layout(PyWM[View], Animate[PyWMDownstreamState]):
    def __init__(self, debug: bool=False, config_file: Optional[str]=None) -> None:
        self._config_file = config_file
        load_config(path_str=self._config_file)

        self._debug = debug
        PyWM.__init__(self, View, **conf_pywm(), outputs=conf_outputs(), debug=debug)
        Animate.__init__(self)

        self.mod = conf_mod()
        self.mod_sym = ""
        self._set_mod_sym()

        self.key_processor = KeyProcessor(self.mod_sym)
        self.auth_backend = AuthBackend(self)
        self.panel_launcher = PanelsLauncher()
        self.panel_endpoint = PanelEndpoint(self)

        self.workspaces: list[Workspace] = [Workspace(PyWMOutput("dummy", -1, 1., 1280, 720, (0, 0)), 0, 0, 1280, 720)]

        self.state = LayoutState()

        self.overlay: Optional[Overlay] = None

        self.backgrounds: list[Background] = []
        self.top_bars: list[TopBar] = []
        self.bottom_bars: list[BottomBar] = []
        self.corners: list[list[Corner]] = []
        self.focus_borders: FocusBorders = FocusBorders(self)

        self.thread = LayoutThread(self)

        self._animations: list[Animation] = []

        self._idle_inhibit_user = False

        # Workspace cursor is on, Focused workspace override by focused view
        self._active_workspace: tuple[Workspace, Optional[Workspace]] = self.workspaces[0], None

    def _set_mod_sym(self) -> None:
        self.mod_sym = ""
        if self.mod == PYWM_MOD_ALT:
            self.mod_sym = "Alt"
        elif self.mod == PYWM_MOD_LOGO:
            self.mod_sym = "Super"
        else:
            raise Exception("Unknown mod")

    def _setup_workspaces(self) -> None:
        output_conf = conf_outputs()
        def disable_anim(output: PyWMOutput) -> bool:
            for o in output_conf:
                if o['name'] == output.name:
                    return 'anim' in o and not o['anim']
            return False
        ws = [Workspace(o, o.pos[0], o.pos[1], o.width, o.height, disable_anim(o)) for o in self.layout]
        i, j = 0, len(ws) - 1
        while i < len(ws) and j < len(ws) and i < j:
            if ws[i].swallow(ws[j]):
                del ws[j]
            else:
                if j == i + 1:
                    j = len(ws) - 1
                    i += 1
                else:
                    j -= 1

        for w in self.workspaces:
            best_score = 0.1
            best_ws = None
            for wp in ws:
                if wp._handle >= 0:
                    continue
                score = w.score(wp)
                if score > best_score:
                    best_score = score
                    best_ws = wp
            if best_ws is not None:
                best_ws._handle = w._handle

        self.workspaces = ws
        for w in [w for w in self.workspaces if w._handle < 0]:
            h = 0
            while True:
                if h not in [w._handle for w in self.workspaces]:
                    break
                h+=1
            w._handle = h


        logger.debug("Setup of newm workspaces")
        for w in self.workspaces:
            logger.debug("  %s" % str(w))

        self.state = self.state.with_workspaces(self)
        self._update_active_workspace()


    def _update_active_workspace(self) -> None:
        # Clean
        ws_check1, ws_check2 = self._active_workspace
        if ws_check1._handle not in [w._handle for w in self.workspaces]:
            ws_check1 = self.workspaces[0]
        if ws_check2 is not None and ws_check2._handle not in [w._handle for w in self.workspaces]:
            ws_check2 = None
        self._active_workspace = ws_check1, ws_check2

        # Find ws cursor is on
        ws: Optional[Workspace] = None
        for w in self.workspaces:
            if w.pos_x <= self.cursor_pos[0] < w.pos_x + w.width and w.pos_y <= self.cursor_pos[1] < w.pos_y + w.height:
                ws = w
                break

        # Possibly update ws after cursor move
        if ws is None:
            logger.warn("Workspaces do not cover whole area")
        else:
            ws_old, _ = self._active_workspace
            if ws_old != ws:
                self._active_workspace = ws, None

    def _setup_widgets(self) -> None:
        def get_workspace_for_output(output: PyWMOutput) -> Workspace:
            for w in self.workspaces:
                if w.pos_x <= output.pos[0] < w.pos_x + w.width and w.pos_y <= output.pos[1] < w.pos_y + w.height:
                    return w
            logger.warn("Workspaces do not cover whole area")
            return self.workspaces[0]

        for b in self.bottom_bars:
            b.stop()
            b.destroy()
        self.bottom_bars = []

        for t in self.top_bars:
            t.stop()
            t.destroy()
        self.top_bars = []

        for bg in self.backgrounds:
            bg.destroy()
        self.backgrounds = []

        for c in self.corners:
            for c2 in c:
                c2.destroy()
        self.corners = []

        if conf_bar_enabled():
            self.bottom_bars = [self.create_widget(BottomBar, o) for o in self.layout]
            self.top_bars = [self.create_widget(TopBar, o) for o in self.layout]
        else:
            self.bottom_bars = []
            self.top_bars = []

        self.backgrounds = [self.create_widget(Background, o, get_workspace_for_output(o)) for o in self.layout]

        for o in self.layout:
            self.corners += [[
                self.create_widget(Corner, o, True, True),
                self.create_widget(Corner, o, True, False),
                self.create_widget(Corner, o, False, True),
                self.create_widget(Corner, o, False, False)
            ]]

        self.focus_borders.update()

        self.damage()

    def _setup(self, fallback: bool=True, reconfigure: bool=True) -> None:
        if reconfigure:
            load_config(fallback=fallback, path_str=self._config_file)

        self.mod = conf_mod()
        self._set_mod_sym()

        self.configure_gestures(
            conf_two_finger_min_dist(),
            conf_lp_freq(),
            conf_lp_inertia(),
            conf_validate_threshold())

        self._setup_widgets()

        self.key_processor.clear()
        if (kb := conf_key_bindings()) is not None:
            self.key_processor.register_bindings(
                *kb(self)
            )

        if reconfigure:
            self.reconfigure(dict(**conf_pywm(), outputs=conf_outputs(), debug=self._debug))

    def reducer(self, state: LayoutState) -> PyWMDownstreamState:
        return PyWMDownstreamState(state.lock_perc)

    def animate(self, old_state: LayoutState, new_state: LayoutState, dt: float) -> None:
        cur = self.reducer(old_state)
        nxt = self.reducer(new_state)

        self._animate(LayoutDownstreamInterpolation(self, cur, nxt), dt)

    def process(self) -> PyWMDownstreamState:
        return self._process(self.reducer(self.state))

    def main(self) -> None:
        logger.debug("Layout main...")

        self._setup(reconfigure=False)

        self.thread.start()
        self.panel_endpoint.start()
        self.panel_launcher.start()

        # Initially display cursor
        self.update_cursor()

        # Run on_startup
        try:
            conf_on_startup()()
        except Exception:
            logger.exception("on_startup")

        # Fade in
        def fade_in() -> None:
            time.sleep(.5)
            def reducer(state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
                return None, state.copy(background_opacity=1.)
            self.animate_to(reducer, conf_blend_t())
        Thread(target=fade_in).start()

        # Greeter
        if self.auth_backend.is_greeter():
            def greet() -> None:
                while len([p for p in self.panels() if p.panel == "lock"]) < 1:
                    time.sleep(.5)
                self.ensure_locked()
                self.auth_backend.init_session()
            Thread(target=greet).start()


    def _terminate(self) -> None:
        super().terminate()
        self.panel_endpoint.stop()
        self.panel_launcher.stop()

        for t in self.top_bars:
            t.stop()
        for b in self.bottom_bars:
            b.stop()
        if self.thread is not None:
            self.thread.stop()


    def animate_to(self,
                   reducer: Callable[[LayoutState], tuple[Optional[LayoutState], Optional[LayoutState]]],
                   duration: float,
                   then: Optional[Callable[..., None]]=None,
                   overlay_safe: bool=False) -> None:
        self.thread.push(Animation(self, reducer, duration, then, overlay_safe))


    def damage(self) -> None:
        super().damage()

        for _, v in self._views.items():
            v.damage()

        for bg in self.backgrounds:
            bg.damage()

        for t in self.top_bars:
            t.damage()

        for b in self.bottom_bars:
            b.damage()

        self.focus_borders.damage()


    def update(self, new_state: LayoutState) -> None:
        self.state = new_state
        self.damage()

    def _animate_to(self, new_state: LayoutState, duration: float) -> None:
        self.animate(self.state, new_state, duration)

        for _, v in self._views.items():
            v.animate(self.state, new_state, duration)

        for bg in self.backgrounds:
            bg.animate(self.state, new_state, duration)

        for t in self.top_bars:
            t.animate(self.state, new_state, duration)

        for b in self.bottom_bars:
            b.animate(self.state, new_state, duration)

        self.focus_borders.animate(self.state, new_state, duration)


    def _trusted_unlock(self) -> None:
        if self.is_locked():
            def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
                return None, state.copy(lock_perc=0., background_opacity=1.)
            self.animate_to(
                reducer,
                conf_anim_t(),
                lambda: self.update_cursor())


    """
    Utilities
    """

    def __str__(self) -> str:
        return "<Layout %s>" % (self.config)

    def debug_str(self) -> str:
        res = "%s\n  %s\n\n" % (self, str(self.state))
        for w in self.workspaces:
            res += "%s\n      %s\n" % (str(w), self.state.get_workspace_state(w))
        for i, v in self._views.items():
            s = None
            ws_handle = -1
            try:
                s, ws_state, ws_handle = self.state.find_view(v)
            except:
                pass
            res += "%2d: %s on workspace %d\n      %s\n" % (i, v, ws_handle, s)
        return res

    def find_focused_box(self) -> tuple[Workspace, float, float, float, float]:
        try:
            view = self.find_focused_view()
            if view is not None:
                view_state, ws_state, ws_handle = self.state.find_view(view)

            ws = [w for w in self.workspaces if w._handle == ws_handle][0]
            return ws, view_state.i, view_state.j, view_state.w, view_state.h
        except Exception:
            return self.workspaces[0], 0, 0, 1, 1


    def place_initial(self, workspace: Workspace, ws_state: WorkspaceState, w: int, h: int) -> tuple[int, int]:
        """
        Strategy
        - If viewpoint > extent:
            - If first view: Place at 0, 0
            - Otherwise: Enlarge to the top right (if space) or bottom left
        - Else
            - Start at top right visible tile and move to right (alternatively traverse in spiral) to find closest unused tile
        """

        place_i = 0
        place_j = 0

        min_i, min_j, max_i, max_j = ws_state.get_extent()
        min_i = math.floor(min_i)
        min_j = math.floor(min_j)
        max_i = math.floor(max_i)
        max_j = math.floor(max_j)

        view_min_i, view_min_j = ws_state.i, ws_state.j
        view_max_i, view_max_j = ws_state.i + ws_state.size - 1, ws_state.j + ws_state.size - 1
        view_min_i = math.floor(view_min_i)
        view_min_j = math.floor(view_min_j)
        view_max_i = math.ceil(view_max_i)
        view_max_j = math.ceil(view_max_j)

        if len(self.tiles(workspace)) == 0:
            place_i, place_j = 0, 0
        elif (view_max_i - view_min_i) > (max_i - min_i):
            place_i, place_j = max_i + 1, max(min_j, view_min_j)
        elif (view_max_j - view_min_j) > (max_j - min_j):
            place_i, place_j = max(min_i, view_min_i), max_j + 1
        else:
            i, j = ws_state.i, ws_state.j
            for j, i in product(range(math.floor(j),
                                    math.ceil(j + ws_state.size)),
                                range(math.floor(i),
                                    math.ceil(i + ws_state.size))):
                for jp, ip in product(range(j, j + h), range(i, i + w)):
                    if not ws_state.is_tile_free(ip, jp):
                        break
                else:
                    place_i, place_j = i, j
                    break
            else:
                ws_, i_, j_, w_, h_ = self.find_focused_box()
                if ws_._handle != workspace._handle:
                    i_, j_, w_, h_ = 0, 0, 1, 1

                place_i, place_j = round(i_ + w_), round(j_)
                while not ws_state.is_tile_free(place_i, place_j):
                    place_i += 1

        logger.debug("Found initial placement at %d, %d", place_i, place_j)
        return place_i, place_j

    def on_layout_change(self) -> None:
        self._setup_workspaces()
        self._setup_widgets()

    def on_key(self, time_msec: int, keycode: int, state: int, keysyms: str) -> bool:
        # BEGIN DEBUG
        if self.modifiers & self.mod > 0 and keysyms == "D":
            self.force_close_overlay()
            return True
        # END DEBUG

        if self.overlay is not None and self.overlay.ready():
            logger.debug("...passing to overlay %s", self.overlay)
            if self.overlay.on_key(time_msec, keycode, state, keysyms):
                return True

        return self.key_processor.on_key(state == PYWM_PRESSED,
                                         keysyms,
                                         self.modifiers,
                                         self.mod,
                                         self.is_locked())

    def on_modifiers(self, modifiers: int) -> bool:
        if self.is_locked():
            return False

        if self.modifiers & self.mod > 0:
            """
            This is a special case, if a SingleFingerMoveGesture has started, then
            Mod is pressed the MoveResize(Floating)Overlay is not triggered - we reallow a
            gesture

            If a gesture has been captured reallow_gesture is a noop
            """
            logger.debug("Resetting gesture")
            self.reallow_gesture()

        if self.overlay is not None and self.overlay.ready():
            if self.overlay.on_modifiers(modifiers):
                return True
        return False

    def on_motion(self, time_msec: int, delta_x: float, delta_y: float) -> bool:
        self._update_active_workspace()
        if self.is_locked():
            return False

        if self.overlay is not None and self.overlay.ready():
            return self.overlay.on_motion(time_msec, delta_x, delta_y)

        return False

    def on_button(self, time_msec: int, button: int, state: int) -> bool:
        if self.is_locked():
            return False

        if self.overlay is not None and self.overlay.ready():
            return self.overlay.on_button(time_msec, button, state)

        return False

    def on_axis(self, time_msec: int, source: int, orientation: int, delta: float, delta_discrete: int) -> bool:
        if self.is_locked():
            return False

        if self.overlay is not None and self.overlay.ready():
            return self.overlay.on_axis(time_msec, source, orientation,
                                        delta, delta_discrete)

        return False

    def on_gesture(self, gesture: Gesture) -> bool:
        if self.is_locked():
            return False

        logger.debug("Gesture %s...", gesture)
        if self.overlay is not None and self.overlay.ready():
            logger.debug("...passing to overlay %s", self.overlay)
            return self.overlay.on_gesture(gesture)
        elif self.overlay is None:
            if self.modifiers & self.mod and \
                    (isinstance(gesture, TwoFingerSwipePinchGesture) or
                     isinstance(gesture, SingleFingerMoveGesture)):
                logger.debug("...MoveResize")
                view = self.find_focused_view()

                ovr: Optional[Overlay] = None
                if view is not None and view.is_float(self.state):
                    ovr = MoveResizeFloatingOverlay(self, view)
                    ovr.on_gesture(gesture)
                    self.enter_overlay(ovr)
                    return True

                elif view is not None and view.is_tiled(self.state):
                    ovr = MoveResizeOverlay(self, view)
                    ovr.on_gesture(gesture)
                    self.enter_overlay(ovr)
                    return True

            if isinstance(gesture, HigherSwipeGesture) \
                    and gesture.n_touches == 3:
                logger.debug("...Swipe")
                ovr = SwipeOverlay(self)
                ovr.on_gesture(gesture)
                self.enter_overlay(ovr)
                return True

            if not self.state.get_workspace_state(self.get_active_workspace()).is_in_overview():
                if isinstance(gesture, HigherSwipeGesture) \
                        and gesture.n_touches == 4:
                    logger.debug("...SwipeToZoom")
                    ovr = SwipeToZoomOverlay(self)
                    ovr.on_gesture(gesture)
                    self.enter_overlay(ovr)
                    return True

            if isinstance(gesture, HigherSwipeGesture) \
                    and gesture.n_touches == 5:
                logger.debug("...Launcher")
                ovr = LauncherOverlay(self)
                ovr.on_gesture(gesture)
                self.enter_overlay(ovr)
                return True

        return False


    def on_idle(self, elapsed: float, idle_inhibited: bool) -> None:
        idle_inhibited = idle_inhibited or self._idle_inhibit_user

        if idle_inhibited and elapsed > 0:
            return

        if elapsed == 0:
            conf_idle_callback()("active")
        elif len(conf_idle_times()) > 2 and elapsed > conf_idle_times()[2]:
            conf_idle_callback()("idle-suspend")
            os.system(conf_suspend_command())
        elif len(conf_idle_times()) > 1 and elapsed > conf_idle_times()[1]:
            conf_idle_callback()("idle-lock")
            self.ensure_locked()
        elif len(conf_idle_times()) > 0 and elapsed > conf_idle_times()[0]:
            conf_idle_callback()("idle")

    def on_wakeup(self) -> None:
        if conf_lock_on_wakeup():
            self.ensure_locked()

    def enter_overlay(self, overlay: Overlay) -> None:
        self.thread.push(overlay)

    def start_overlay(self, overlay: Overlay) -> None:
        logger.debug("Going to enter %s...", overlay)
        self.key_processor.on_other_action()
        self.overlay = overlay
        self.overlay.init()

    # BEGIN DEBUG
    def force_close_overlay(self) -> None:
        if self.overlay is None:
            return

        logger.debug("Force-closing %s", self.overlay)
        try:
            self.overlay.destroy()
        finally:
            self.overlay = None
    # END DEBUG


    def exit_overlay(self) -> None:
        logger.debug("Going to exit overlay...")
        if self.overlay is None:
            logger.debug("...aborted")
            return

        logger.debug("...destroy")
        self.overlay.destroy()

    def on_overlay_destroyed(self) -> None:
        logger.debug("Overlay destroyed")
        self.thread.on_overlay_destroyed()
        self.overlay = None

        logger.debug("Resetting gesture")
        self.reallow_gesture()


    def destroy_view(self, view: View) -> None:
        logger.info("Destroying view %s", view)
        state = None
        ws_state = None
        try:
            state, ws_state, ws_handle = self.state.find_view(view)
        except:
            """
            This can happen if the view has not been mapped (view.show) when it is destroyed
            """
            return

        best_view: Optional[int] = None
        if view.is_focused():
            logger.debug("Finding view to focus since %s closes...", view)
            if view.parent is not None:
                p = cast(View, view.parent)
                while not p.is_tiled(self.state) and p.parent is not None:
                    p = cast(View, p.parent)
                if p is not None:
                    best_view = p._handle

            if best_view is None:
                best_view_score = 1000.
                for k, s in ws_state._view_states.items():
                    if not s.is_tiled:
                        continue

                    if k == view._handle:
                        continue

                    i, j, w, h = state.i, state.j, state.w, state.h
                    if state.is_layer:
                        i, j = ws_state.i + .5*ws_state.size, ws_state.j + .5*ws_state.size
                        w, h = 0, 0
                    elif not state.is_tiled:
                        i, j = state.float_pos
                        w, h = 0, 0

                    sc = (s.i - i + s.w / 2. - w / 2.)**2 + (s.j - j + s.h / 2. - h / 2.)**2
                    logger.debug("View (%d) has score %f", k, sc)
                    if sc < best_view_score:
                        best_view_score = sc
                        best_view = k

        if best_view is not None and best_view in self._views:
            logger.debug("Found view to focus: %s" % self._views[best_view])
            bv: int = best_view
            def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
                try:
                    state = state\
                        .focusing_view(self._views[bv])\
                        .without_view_state(view)\
                        .constrain()

                    self.focus_borders.update_focus(self._views[bv], present_states=(None, state))
                    self._views[bv].focus()

                except:
                    """
                    View might not exist anymore
                    """
                    state = state\
                        .copy()\
                        .without_view_state(view)\
                        .constrain()

                    self.focus_borders.unfocus()

                return None, state

            self.animate_to(
                reducer,
                conf_anim_t())
        else:
            if view.is_focused():
                self.focus_borders.unfocus()
            self.animate_to(
                lambda state: (None, state
                    .copy()
                    .without_view_state(view)
                    .constrain()),
                conf_anim_t())

    def focus_hint(self, view: View) -> None:
        try:
            _, __, ws_handle = self.state.find_view(view)
            ws = [w for w in self.workspaces if w._handle == ws_handle][0]
            ws.focus_view_hint = view._handle

            ws_a, ws_a_old = self._active_workspace
            self._active_workspace = ws_a, ws

        except Exception:
            logger.warn("Missing state: %s" % self)

    def command(self, cmd: str, arg: Optional[str]=None) -> Optional[str]:
        logger.debug(f"Received command {cmd}")

        def set_inhibit_idle(status: bool) -> None:
            self._idle_inhibit_user = status

        def lock() -> None:
            self._update_idle(True)
            self.ensure_locked(anim=False)

        def clean() -> None:
            def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
                new_state = state.copy().clean(list(self._views.keys()))
                return None, new_state
            self.animate_to(reducer, conf_anim_t())

        cmds: dict[str, Callable[[], Optional[str]]] = {
            "lock": self.ensure_locked,
            "lock-pre": lambda: self.ensure_locked(anim=False),
            "lock-post": lock,
            "config": print_config,
            "debug": self.debug_str,
            "inhibit-idle": lambda: set_inhibit_idle(True),
            "finish-inhibit-idle": lambda: set_inhibit_idle(False),
            "close-launcher": lambda: self.exit_overlay() if isinstance(self.overlay, LauncherOverlay) else None,
            "open-virtual-output": lambda: self.open_virtual_output(arg) if arg is not None else None,
            "close-virtual-output": lambda: self.close_virtual_output(arg) if arg is not None else None,
            "clean": clean
        }
        return cmds.get(cmd, lambda: f"Unknown command {cmd}")()

    def launch_app(self, cmd: str) -> None:
        """
        Should be LauncherOverlay
        """
        self.exit_overlay()
        os.system("%s &" % cmd)

    def is_view_on_workspace(self, view: View, workspace: Optional[Workspace]) -> bool:
        if workspace is None:
            return True
        try:
            _, __, ws_handle = self.state.find_view(view)
            return workspace._handle == ws_handle
        except Exception:
            logger.warn("Missing state: %s" % self)
            return False


    """
    API to be used for configuration
    1. Getters
    """
    def get_active_workspace(self) -> Workspace:
        if self._active_workspace[1] is not None:
            return self._active_workspace[1]
        return self._active_workspace[0]

    def tiles(self, workspace: Optional[Workspace]=None) -> list[View]:
        return [v for _, v in self._views.items() if v.is_tiled(self.state) and self.is_view_on_workspace(v, workspace)]

    def floats(self, workspace: Optional[Workspace]=None) -> list[View]:
        return [v for _, v in self._views.items() if v.is_float(self.state) and self.is_view_on_workspace(v, workspace)]

    def panels(self, workspace: Optional[Workspace]=None) -> list[View]:
        return [v for _, v in self._views.items() if v.is_panel() and self.is_view_on_workspace(v, workspace)]

    def views(self, workspace: Optional[Workspace]=None) -> list[View]:
        return [v for _, v in self._views.items() if not v.is_panel() and self.is_view_on_workspace(v, workspace)]

    def find_focused_view(self) -> Optional[View]:
        for _, view in self._views.items():
            if view.is_focused():
                return view

        return None

    """
    2. General purpose methods
    """
    def update_config(self) -> None:
        self._setup(fallback=False)
        self.damage()

        conf_on_reconfigure()()

    def ensure_locked(self, anim: bool=True, dim: bool=False) -> None:
        def focus_lock() -> None:
            lock_screen = [v for v in self.panels() if v.panel == "lock"]
            if len(lock_screen) > 0:
                lock_screen[0].focus()
            else:
                logger.exception("Locking without lock panel - not a good idea")

        self.auth_backend.lock()

        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
            return None if anim else state.copy(lock_perc=1., background_opacity=.5), state.copy(lock_perc=1., background_opacity=.5)
        self.animate_to(
            reducer,
            conf_anim_t(), focus_lock)

        if dim:
            conf_idle_callback()("lock")

    def terminate(self) -> None:
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            return state.copy(final=True), state.copy(final=True, background_opacity=0.)
        self.animate_to(reducer, conf_blend_t(), self._terminate)

    """
    3. Change global or workspace state / move viewpoint
    """
    def enter_launcher_overlay(self) -> None:
        self.enter_overlay(LauncherOverlay(self))

    def toggle_overview(self, only_active_workspace: bool=False) -> None:
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            if only_active_workspace:
                overview = not state.get_workspace_state(self.get_active_workspace()).is_in_overview()
            else:
                overview = not state.all_in_overview()

            focused: Optional[View] = None
            if not overview:
                focused = self.find_focused_view()
            return None, state.with_overview_set(overview, None if not only_active_workspace else self.get_active_workspace(), focused)
        self.animate_to(reducer, conf_anim_t())

    def toggle_fullscreen(self, defined_state: Optional[bool] = None) -> None:
        active_ws = self.get_active_workspace()
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            if state.get_workspace_state(self.get_active_workspace()).is_in_overview():
                state = state.with_overview_set(False, only_workspace=self.get_active_workspace())

            view = self.find_focused_view()

            if view is not None and not view.is_tiled(state):
                view = None

            if view is not None:
                while view.parent is not None and not view.is_tiled(state):
                    view = cast(View, view.parent)

            ws: Optional[Workspace] = None
            ws_state: Optional[WorkspaceState] = None
            if view is not None:
                view_state, ws_state, ws_handle = state.find_view(view)
                ws = [w for w in self.workspaces if w._handle == ws_handle][0]
            else:
                ws = active_ws
                ws_state = state.get_workspace_state(active_ws)

            fs = ws_state.is_fullscreen()
            if fs == defined_state:
                return None, None

            if conf_send_fullscreen_to_views():
                for v in self.tiles():
                    v.set_fullscreen(not fs)

            if fs:
                return None, state.setting_workspace_state(ws, ws_state.without_fullscreen())
            elif view is not None:
                return None, state.setting_workspace_state(ws, ws_state.with_fullscreen(view))
            else:
                return None, None
        self.animate_to(reducer, conf_anim_t())

    def basic_move(self, delta_i: int, delta_j: int) -> None:
        ws = self.get_active_workspace()
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
            ws_state = state.get_workspace_state(ws)
            return None, state.replacing_workspace_state(ws, i=ws_state.i+delta_i, j=ws_state.j+delta_j)
        self.animate_to(reducer, conf_anim_t())

    def basic_scale(self, delta_s: int) -> None:
        ws = self.get_active_workspace()
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
            ws_state = state.get_workspace_state(ws)
            return None, state.replacing_workspace_state(ws, size=max(1, ws_state.size+delta_s))
        self.animate_to(reducer, conf_anim_t())

    """
    4. Change focus
    """
    def focus_view(self, view: View) -> None:
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
            view.focus()
            return None, state.focusing_view(view)
        self.animate_to(reducer, conf_anim_t())

    def move_in_stack(self, delta: int) -> None:
        view = self.find_focused_view()
        if view is None:
            return

        try:
            view_state, ws_state, ws_handle = self.state.find_view(view)
            ws = [w for w in self.workspaces if w._handle == ws_handle][0]
            sid, idx, siz = view_state.stack_data
            nidx = (idx+1)%siz
            next_view = [k for k, s in ws_state._view_states.items() if s.stack_data[0] == sid and s.stack_data[1]==nidx]
            if len(next_view) > 0 and next_view[0] != view:
                self._views[next_view[0]].focus()
        except:
            logger.exception("Unexpected")


    def move(self, delta_i: int, delta_j: int) -> None:
        ws, i, j, w, h = self.find_focused_box()
        ws_state = self.state.get_workspace_state(ws)

        if ((i + w > ws_state.i + ws_state.size and delta_i > 0) or
                (i < ws_state.i and delta_i < 0) or
                (j + h > ws_state.j + ws_state.size and delta_j > 0) or
                (j < ws_state.j and delta_j < 0)):

            vf = self.find_focused_view()
            if vf is not None:
                self.focus_view(vf)
                return


        best_view = None
        best_view_score = 1000.

        for k, s in ws_state._view_states.items():
            if not s.is_tiled:
                continue

            sc = _score(i, j, w, h, delta_i, delta_j, s.i, s.j, s.w, s.h)
            if sc < best_view_score:
                best_view_score = sc
                best_view = k

        if best_view is not None:
            self.focus_view(self._views[best_view])

    def move_next_view(self, dv: int=1, active_workspace: bool=True) -> None:
        views = self.views(self.get_active_workspace() if active_workspace else None)
        focused_view = self.find_focused_view()

        if focused_view is not None and focused_view in views:
            idx = views.index(focused_view)
            next_view = views[(idx + dv)%len(views)]
            self.focus_view(next_view)
        elif len(views) > 0:
            self.focus_view(views[0])

    def move_workspace(self, ds: int=1) -> None:
        ws = self.get_active_workspace()
        i, ws = [(i, w) for i, w in enumerate(self.workspaces) if w._handle == ws._handle][0]

        i = (i + ds) % len(self.workspaces)
        ws_new = self.workspaces[i]

        views = self.views(ws_new)
        if ws_new.focus_view_hint is not None:
            view = [v for v in views if v._handle == ws_new.focus_view_hint]
            if len(view) == 1:
                self.focus_view(view[0])
                return

        if len(views) > 0:
            self.focus_view(views[0])

    """
    5. Change focused view
    """
    def close_focused_view(self) -> None:
        view = [v for _, v in self._views.items() if v.is_focused()]
        if len(view) == 0:
            return

        view[0].close()

    def toggle_focused_view_floating(self) -> None:
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            view = self.find_focused_view()
            if view is not None:
                try:
                    s, ws_state, ws_handle = state.find_view(view)
                    ws = [w for w in self.workspaces if w._handle == ws_handle][0]
                    s1, s2 = view.toggle_floating(s, ws, ws_state)

                    ws_state1 = ws_state.with_view_state(view, **s1.__dict__)
                    ws_state2 = ws_state.replacing_view_state(view, **s2.__dict__)
                    ws_state2.validate_stack_indices(view)

                    return (state.setting_workspace_state(ws, ws_state1), state.setting_workspace_state(ws, ws_state2))
                except:
                    return (None, state)
            else:
                return (None, state)
        self.animate_to(reducer, conf_anim_t())

    def change_focused_view_workspace(self, ds: int=1) -> None:
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            view = self.find_focused_view()
            if view is not None:
                try:
                    s, ws_state, ws_handle = state.find_view(view)
                    i, ws = [(i, w) for i, w in enumerate(self.workspaces) if w._handle == ws_handle][0]

                    if not s.is_tiled:
                        return None, None

                    i = (i + ds) % len(self.workspaces)
                    ws_new = self.workspaces[i]
                    ws_state = state.get_workspace_state(ws_new)

                    if ws == ws_new:
                        return None, None

                    state = state.without_view_state(view)
                    state0, state1 = view._show_tiled(ws_new, state, ws_state)
                    return (state0, state1)
                except:
                    return (None, state)
            else:
                return (None, state)
        self.animate_to(reducer, conf_anim_t())

    def move_focused_view(self, di: int, dj: int) -> None:
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            view = self.find_focused_view()
            if view is not None:
                try:
                    s, ws_state, ws_handle = state.find_view(view)
                    ws = [w for w in self.workspaces if w._handle == ws_handle][0]
                    ws_state = ws_state.replacing_view_state(view, i=s.i+di, j=s.j+dj).focusing_view(view)
                    ws_state.validate_stack_indices(view)
                    return (None, state.setting_workspace_state(ws, ws_state))
                except:
                    return (None, state)
            else:
                return (None, state)
        self.animate_to(reducer, conf_anim_t())

    def resize_focused_view(self, di: int, dj: int) -> None:
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            view = self.find_focused_view()
            if view is not None:
                try:
                    s = state.get_view_state(view)
                    i, j, w, h = s.i, s.j, s.w, s.h
                    w += di
                    h += dj
                    if w == 0:
                        w = 2
                        i -= 1
                    if h == 0:
                        h = 2
                        j -= 1

                    s, ws_state, ws_handle = state.find_view(view)
                    ws = [w for w in self.workspaces if w._handle == ws_handle][0]
                    ws_state = ws_state.replacing_view_state(view, i=i, j=j, w=w, h=h).focusing_view(view)
                    state.validate_stack_indices(view)
                    return (None, state.setting_workspace_state(ws, ws_state))
                except:
                    return (None, state)
            else:
                return (None, state)
        self.animate_to(reducer, conf_anim_t())


    """
    6. Legacy
    """
    def close_view(self) -> None:
        self.close_focused_view()
