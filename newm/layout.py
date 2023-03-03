from __future__ import annotations

import logging
import math
import os
import time
from itertools import product
from threading import Thread
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar, Union, cast

from pywm import (PYWM_MOD_CTRL, PYWM_PRESSED, PyWM, PyWMDownstreamState,
                  PyWMModifiers, PyWMOutput)

from .animate import Animatable, Animate
from .auth_backend import AuthBackend
from .config import configured_value, load_config, print_config
from .dbus import DBusEndpoint, DBusGestureProvider
from .gestures import Gesture
from .gestures.provider import (CGestureProvider, GestureProvider,
                                PyEvdevGestureProvider)
from .interpolation import LayoutDownstreamInterpolation
from .key_processor import KeyProcessor
from .overlay import (LauncherOverlay, MoveResizeFloatingOverlay,
                      MoveResizeOverlay, Overlay, SwipeOverlay,
                      SwipeToZoomOverlay)
from .panel_launcher import PanelsLauncher
from .state import LayoutState, WorkspaceState
from .view import View
from .widget import Background, BottomBar, Corner, FocusBorders, TopBar
from .workspace import Workspace

logger = logging.getLogger(__name__)

conf_pywm = configured_value("pywm", cast(dict[str, Any], {}))

conf_outputs = configured_value("outputs", cast(list[dict[str, Any]], []))

conf_send_fullscreen_to_views = configured_value("view.send_fullscreen", True)

if TYPE_CHECKING:
    TKeyBindings = Callable[[Layout], list[tuple[str, Callable[[], None]]]]
else:
    TKeyBindings = TypeVar("TKeyBindings")

conf_key_bindings = configured_value(
    "key_bindings", cast(TKeyBindings, lambda layout: [])
)

conf_anim_t = configured_value("anim_time", 0.3)
conf_blend_t = configured_value("blend_time", 1.0)

conf_idle_times = configured_value("energy.idle_times", [120, 300, 600])
conf_suspend_command = configured_value("energy.suspend_command", "systemctl suspend")

"""
code == 'lock': Called on lock - idea is to dim the screen now
code == 'idle': Called after idle_times[0] has passed
code == 'idle-lock': Called after idle_times[1] has passed - the screen is locked additionally
code == 'idle-presuspend': Called after idle_times[2]-5sec has passed - the computer is going to suspend
code == 'idle-suspend': Called after idle_times[2] has passed - the computer is suspended additionally
code == 'active': Called on activity after idle
code == 'sleep': Called on sleep - maybe set backlight to zero
code == 'wakeup': Called on wakeup - maybe blend backlight in (may be called twice)
"""
conf_idle_callback = configured_value("energy.idle_callback", lambda code: None)

conf_on_startup = configured_value("on_startup", lambda: None)
conf_on_reconfigure = configured_value("on_reconfigure", lambda: None)
conf_lock_on_wakeup = configured_value("lock_on_wakeup", True)

conf_native_top_bar_enabled = configured_value("panels.top_bar.native.enabled", False)
conf_native_bottom_bar_enabled = configured_value(
    "panels.bottom_bar.native.enabled", False
)

conf_synchronous_update = configured_value("synchronous_update", lambda: None)

conf_enable_pyevdev_gestures = configured_value("gestures.pyevdev.enabled", False)
conf_enable_c_gestures = configured_value("gestures.c.enabled", True)
conf_enable_dbus_gestures = configured_value("gestures.dbus.enabled", True)

conf_enable_unlock_command = configured_value("enable_unlock_command", True)

conf_gesture_binding_swipe_to_zoom = configured_value(
    "gesture_bindings.swipe_to_zoom", (None, "swipe-4")
)
conf_gesture_binding_swipe = configured_value(
    "gesture_bindings.swipe", (None, "swipe-3")
)
conf_gesture_binding_move_resize = configured_value(
    "gesture_bindings.move_resize", ("L", "move-1", "swipe-2")
)
conf_gesture_binding_launcher = configured_value(
    "gesture_bindings.launcher", (None, "swipe-5")
)


def _score(
    i1: float,
    j1: float,
    w1: float,
    h1: float,
    im: int,
    jm: int,
    i2: float,
    j2: float,
    w2: float,
    h2: float,
) -> float:
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
    At this point: Either im == 1, jm == 0 or im == jm == 1
    """
    d_i = i2 - (i1 + w1)
    if d_i < 0:
        return 1000

    if jm == 1:
        d_j = j2 - (j1 + h1)
        if d_j < 0:
            return 1000

        return d_i + d_j

    else:
        d_j = 0.0
        if j2 >= j1 + h1:
            d_j = j2 - (j1 + h1)
        elif j1 >= j2 + h2:
            d_j = j1 - (j2 + h2)
        else:
            d_j = -1

        return d_i + d_j


class Animation:
    def __init__(
        self,
        layout: Layout,
        reducer: Callable[
            [LayoutState], tuple[Optional[LayoutState], Optional[LayoutState]]
        ],
        duration: float,
        then: Optional[Callable[..., None]],
        overlay_safe: bool = False,
    ) -> None:
        super().__init__()
        self.layout = layout

        """
        (current state) -> (animation initial state (possibly None), animation final state)
        """
        self.reducer = reducer

        self._initial_state: Optional[LayoutState] = None
        self._final_state: Optional[LayoutState] = None
        self._started: bool = False
        self._finish: Optional[float] = None

        # Prevent devision by zero
        self.duration = max(0.1, duration)

        self.then = then
        self.overlay_safe = overlay_safe

    def check_finished(self) -> bool:
        if self._started is not None and self._final_state is None:
            if callable(self.then):
                self.then()
            self.layout.do_flush_animation()
            return True

        if self._started and self._finish is None:
            self._finish = self.layout.get_final_time()

        if self._finish is not None and time.time() > self._finish:
            if self._final_state is not None:
                self.layout.update(self._final_state)
            if callable(self.then):
                self.then()

            self.layout.do_flush_animation()
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

        self._started = True
        if self._final_state is not None:
            # Enforce constraints on final state
            self._final_state.constrain_and_validate()

            if self._final_state == self.layout.state:
                logger.debug("Skipping moot animation")
                self._final_state = None
            else:
                self.layout._animate_to(self._final_state, self.duration)

        else:
            logger.debug("Animation decided not to take place anymore")

    def __str__(self) -> str:
        return "%s -> %s (%f%s)" % (
            self._initial_state,
            self._final_state,
            self.duration,
            ", then" if self.then is not None else "",
        )


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
            if (
                self._current_ovr is not None
                or len([x for x in self._pending if isinstance(x, Overlay)]) > 0
            ):
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
        self.layout.exit_constant_damage()

    def run(self) -> None:
        while self._running:
            try:
                if len(self._pending) > 0:
                    if isinstance(self._pending[0], Overlay):
                        if self._current_anim is None and self._current_ovr is None:
                            logger.debug("Thread: Starting overlay...")
                            self._current_ovr = self._pending.pop(0)
                            self.layout.start_overlay(self._current_ovr)
                            self.layout.enter_constant_damage()
                    else:
                        if self._current_anim is None and (
                            self._current_ovr is None or self._pending[0].overlay_safe
                        ):
                            logger.debug("Thread: Starting animation...")
                            self._current_anim = self._pending.pop(0)
                            self._current_anim.start()
                            self.layout.enter_constant_damage()

                if self._current_anim is not None:
                    if self._current_anim.check_finished():
                        logger.debug("Thread: Finishing animation...")
                        self._current_anim = None
                        self.layout.exit_constant_damage()

                conf_synchronous_update()()
            except Exception:
                logger.exception("Unexpected during LayoutThread")

            time.sleep(1.0 / 30.0)


class Layout(PyWM[View], Animate[PyWMDownstreamState], Animatable):
    def __init__(self, debug: bool = False, config_file: Optional[str] = None) -> None:
        self._config_file = config_file
        load_config(path_str=self._config_file)

        self._debug = debug
        PyWM.__init__(self, View, **conf_pywm(), outputs=conf_outputs(), debug=debug)
        Animate.__init__(self)

        self.key_processor = KeyProcessor()
        self.auth_backend = AuthBackend(self)
        self.panel_launcher = PanelsLauncher()
        self.dbus_endpoint = DBusEndpoint(self)

        self.gesture_providers: list[GestureProvider] = []

        self.workspaces: list[Workspace] = [
            Workspace(PyWMOutput("dummy", -1, 1.0, 1280, 720, (0, 0)), 0, 0, 1280, 720)
        ]

        self.state = LayoutState(self)

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
        self._active_workspace: tuple[Workspace, Optional[Workspace]] = (
            self.workspaces[0],
            None,
        )

    def _setup_workspaces(self) -> None:
        output_conf = conf_outputs()

        def disable_anim(output: PyWMOutput) -> bool:
            for o in output_conf:
                if o["name"] == output.name:
                    return "anim" in o and not o["anim"]
            return False

        ws = [
            Workspace(o, o.pos[0], o.pos[1], o.width, o.height, disable_anim(o))
            for o in self.layout
        ]
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
                h += 1
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
        if ws_check2 is not None and ws_check2._handle not in [
            w._handle for w in self.workspaces
        ]:
            ws_check2 = None
        self._active_workspace = ws_check1, ws_check2

        # Find ws cursor is on
        ws: Optional[Workspace] = None
        for w in self.workspaces:
            if (
                w.pos_x <= self.cursor_pos[0] < w.pos_x + w.width
                and w.pos_y <= self.cursor_pos[1] < w.pos_y + w.height
            ):
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
                if (
                    w.pos_x <= output.pos[0] < w.pos_x + w.width
                    and w.pos_y <= output.pos[1] < w.pos_y + w.height
                ):
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

        if conf_native_bottom_bar_enabled():
            self.bottom_bars = [self.create_widget(BottomBar, o) for o in self.layout]
        else:
            self.bottom_bars = []

        if conf_native_top_bar_enabled():
            self.top_bars = [self.create_widget(TopBar, o) for o in self.layout]
        else:
            self.top_bars = []

        self.backgrounds = [
            self.create_widget(Background, o, get_workspace_for_output(o))
            for o in self.layout
        ]

        for o in self.layout:
            self.corners += [
                [
                    self.create_widget(Corner, o, True, True),
                    self.create_widget(Corner, o, True, False),
                    self.create_widget(Corner, o, False, True),
                    self.create_widget(Corner, o, False, False),
                ]
            ]

        self.focus_borders.update()

        self.damage()

    def _setup(self, reconfigure: bool = True) -> None:
        self._setup_widgets()

        self.key_processor.clear()
        if (kb := conf_key_bindings()) is not None:
            self.key_processor.register_bindings(*kb(self))

        # Stop and re-setup Gestures
        for g in self.gesture_providers:
            g.stop()
        self.gesture_providers = []

        dbus_gesture_provider: Optional[DBusGestureProvider] = None
        if conf_enable_dbus_gestures():
            dbus_gesture_provider = DBusGestureProvider(
                self.dbus_endpoint, self._gesture_provider_callback
            )
            self.dbus_endpoint.set_gesture_provider(dbus_gesture_provider)

        self.gesture_providers = (
            cast(
                list[GestureProvider],
                [PyEvdevGestureProvider(self._gesture_provider_callback)]
                if conf_enable_pyevdev_gestures()
                else [],
            )
            + cast(
                list[GestureProvider],
                [CGestureProvider(self._gesture_provider_callback)]
                if conf_enable_c_gestures()
                else [],
            )
            + cast(
                list[GestureProvider],
                [dbus_gesture_provider] if dbus_gesture_provider is not None else [],
            )
        )

        # Start gesture providers
        for p in self.gesture_providers:
            p.start()

        if reconfigure:
            self.reconfigure(
                dict(**conf_pywm(), outputs=conf_outputs(), debug=self._debug)
            )

            for v in self._views.values():
                v.update()

    def reducer(self, state: LayoutState) -> PyWMDownstreamState:
        return PyWMDownstreamState(state.lock_perc)

    def animate(
        self, old_state: LayoutState, new_state: LayoutState, dt: float
    ) -> None:
        cur = self.reducer(old_state)
        nxt = self.reducer(new_state)

        self._animate(LayoutDownstreamInterpolation(self, cur, nxt), dt)

    def process(self) -> PyWMDownstreamState:
        return self._process(self.reducer(self.state))

    def main(self) -> None:
        logger.debug("Layout main...")

        self._setup(reconfigure=False)

        self.thread.start()
        self.panel_launcher.start()
        self.dbus_endpoint.start()

        # Initially display cursor
        self.update_cursor()

        # Run on_startup
        try:
            conf_on_startup()()
        except Exception:
            logger.exception("on_startup")

        # Fade in
        def fade_in() -> None:
            time.sleep(0.5)

            def reducer(
                state: LayoutState,
            ) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
                return None, state.copy(background_opacity=1.0)

            self.animate_to(reducer, conf_blend_t())

        Thread(target=fade_in).start()

        # Greeter
        if self.auth_backend.is_greeter():

            def greet() -> None:
                while len([p for p in self.panels() if p.panel == "lock"]) < 1:
                    time.sleep(0.5)
                self.ensure_locked()
                self.auth_backend.init_session()

            Thread(target=greet).start()

    def _terminate(self) -> None:
        super().terminate()
        self.dbus_endpoint.stop()
        self.panel_launcher.stop()
        for p in self.gesture_providers:
            p.stop()

        for t in self.top_bars:
            t.stop()
        for b in self.bottom_bars:
            b.stop()
        if self.thread is not None:
            self.thread.stop()

    def animate_to(
        self,
        reducer: Callable[
            [LayoutState], tuple[Optional[LayoutState], Optional[LayoutState]]
        ],
        duration: float,
        then: Optional[Callable[..., None]] = None,
        overlay_safe: bool = False,
    ) -> None:
        self.thread.push(Animation(self, reducer, duration, then, overlay_safe))

    def update(self, new_state: LayoutState) -> None:
        self.state = new_state
        self.damage()

    def _all_animates(self) -> list[Animatable]:
        return [
            self,
            *self._views.values(),
            *self.backgrounds,
            *self.top_bars,
            *self.bottom_bars,
            self.focus_borders,
        ]

    def do_flush_animation(self) -> None:
        for a in self._all_animates():
            a.flush_animation()

    def _animate_to(self, new_state: LayoutState, duration: float) -> None:
        for a in self._all_animates():
            a.animate(self.state, new_state, duration)

    def _anim_damage(self) -> None:
        self.damage(False)

    def _trusted_unlock(self) -> None:
        if self.is_locked():

            def reducer(
                state: LayoutState,
            ) -> tuple[Optional[LayoutState], LayoutState]:
                return None, state.copy(lock_perc=0.0, background_opacity=1.0)

            self.animate_to(reducer, conf_anim_t(), lambda: self.update_cursor())

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

    def place_initial(
        self, workspace: Workspace, ws_state: WorkspaceState, w: int, h: int
    ) -> tuple[int, int]:
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
        view_max_i, view_max_j = (
            ws_state.i + ws_state.size - 1,
            ws_state.j + ws_state.size - 1,
        )
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
            for j, i in product(
                range(math.floor(j), math.ceil(j + ws_state.size)),
                range(math.floor(i), math.ceil(i + ws_state.size)),
            ):
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

    """
    Input
    """

    def on_key(self, time_msec: int, keycode: int, state: int, keysyms: str) -> bool:
        """
        These are processed via on_modifiers
        """
        if keysyms in ["Super_L", "Super_R", "Alt_L", "Alt_R", "Logo_L", "Logo_R"]:
            return False

        if self.overlay is not None and self.overlay.ready():
            logger.debug("...passing to overlay %s", self.overlay)
            if self.overlay.on_key(time_msec, keycode, state, keysyms):
                return True

        return self.key_processor.on_key(
            state == PYWM_PRESSED, keysyms, self.modifiers, self.is_locked()
        )

    def on_modifiers(
        self, modifiers: PyWMModifiers, last_modifiers: PyWMModifiers
    ) -> bool:
        if modifiers.pressed(last_modifiers).any():
            """
            This is a special case, if a SingleFingerMoveGesture has started, then
            Mod is pressed the MoveResize(Floating)Overlay is not triggered - we re-allow a
            gesture

            If a gesture has been captured reset_gesture is a noop
            """
            logger.debug("Resetting gesture")
            self.reset_gesture()

        if self.is_locked():
            return False

        if self.overlay is not None and self.overlay.ready():
            if self.overlay.on_modifiers(modifiers, last_modifiers):
                return False

        self.key_processor.on_modifiers(modifiers, last_modifiers, self.is_locked())

        """
        Always return False - no matter what key_processor returns. Modifiers should not be captured
        """

        return False

    def on_motion(self, time_msec: int, delta_x: float, delta_y: float) -> bool:
        self._update_active_workspace()
        if self.is_locked():
            return False

        for g in self.gesture_providers:
            res = g.on_pywm_motion(time_msec, delta_x, delta_y)
            if res == 2:
                return True
            if res == 1:
                break

        if self.overlay is not None and self.overlay.ready():
            return self.overlay.on_motion(time_msec, delta_x, delta_y)

        return False

    def on_button(self, time_msec: int, button: int, state: int) -> bool:
        if self.is_locked():
            return False

        if self.overlay is not None and self.overlay.ready():
            return self.overlay.on_button(time_msec, button, state)

        return False

    def on_axis(
        self,
        time_msec: int,
        source: int,
        orientation: int,
        delta: float,
        delta_discrete: int,
    ) -> bool:
        if self.is_locked():
            return False

        for g in self.gesture_providers:
            res = g.on_pywm_axis(time_msec, source, orientation, delta, delta_discrete)
            if res == 2:
                return True
            if res == 1:
                break

        if self.overlay is not None and self.overlay.ready():
            return self.overlay.on_axis(
                time_msec, source, orientation, delta, delta_discrete
            )

        return False

    """
    Gestures
    """

    def on_gesture(
        self, kind: str, time_msec: int, args: list[Union[float, int]]
    ) -> bool:
        for g in self.gesture_providers:
            res = g.on_pywm_gesture(kind, time_msec, args)
            if res == 2:
                return True
            if res == 1:
                break

        return False

    def reset_gesture(self) -> None:
        for g in self.gesture_providers:
            g.reset_gesture()

    def _gesture_provider_callback(self, gesture: Gesture) -> bool:
        if self.is_locked():
            return False

        logger.debug("Gesture %s...", gesture)
        if self.overlay is not None and self.overlay.ready():
            logger.debug("...passing to overlay %s", self.overlay)
            return self.overlay.on_gesture(gesture)
        elif self.overlay is None:
            if self.modifiers.has(conf_gesture_binding_move_resize()[0]) and (
                gesture.kind == conf_gesture_binding_move_resize()[1]
                or gesture.kind == conf_gesture_binding_move_resize()[2]
            ):
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

            if (
                self.modifiers.has(conf_gesture_binding_swipe()[0])
                and gesture.kind == conf_gesture_binding_swipe()[1]
            ):
                logger.debug("...Swipe")
                ovr = SwipeOverlay(self)
                ovr.on_gesture(gesture)
                self.enter_overlay(ovr)
                return True

            if not self.state.get_workspace_state(
                self.get_active_workspace()
            ).is_in_overview():
                if (
                    self.modifiers.has(conf_gesture_binding_swipe_to_zoom()[0])
                    and gesture.kind == conf_gesture_binding_swipe_to_zoom()[1]
                ):
                    logger.debug("...SwipeToZoom")
                    ovr = SwipeToZoomOverlay(self)
                    ovr.on_gesture(gesture)
                    self.enter_overlay(ovr)
                    return True

            if (
                self.modifiers.has(conf_gesture_binding_launcher()[0])
                and gesture.kind == conf_gesture_binding_launcher()[1]
            ):
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
        elif len(conf_idle_times()) > 2 and elapsed > conf_idle_times()[2] - 5.0:
            conf_idle_callback()("idle-presuspend")
        elif len(conf_idle_times()) > 1 and elapsed > conf_idle_times()[1]:
            conf_idle_callback()("idle-lock")
            self.ensure_locked()
        elif len(conf_idle_times()) > 0 and elapsed > conf_idle_times()[0]:
            conf_idle_callback()("idle")

    def on_sleep(self) -> None:
        conf_idle_callback()("sleep")
        if conf_lock_on_wakeup():
            self.ensure_locked(anim=False)

    def on_wakeup(self) -> None:
        conf_idle_callback()("wakeup")
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
        self.reset_gesture()

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
                best_view_score = 1000.0
                for k, s in ws_state._view_states.items():
                    if not s.is_tiled:
                        continue

                    if k == view._handle:
                        continue

                    i, j, w, h = state.i, state.j, state.w, state.h
                    if state.is_layer:
                        i, j = (
                            ws_state.i + 0.5 * ws_state.size,
                            ws_state.j + 0.5 * ws_state.size,
                        )
                        w, h = 0, 0
                    elif not state.is_tiled:
                        i, j = state.float_pos
                        w, h = 0, 0

                    sc = (s.i - i + s.w / 2.0 - w / 2.0) ** 2 + (
                        s.j - j + s.h / 2.0 - h / 2.0
                    ) ** 2
                    logger.debug("View (%d) has score %f", k, sc)
                    if sc < best_view_score:
                        best_view_score = sc
                        best_view = k

        if best_view is not None and best_view in self._views:
            logger.debug("Found view to focus: %s" % self._views[best_view])
            bv: int = best_view

            def reducer(
                state: LayoutState,
            ) -> tuple[Optional[LayoutState], LayoutState]:
                try:
                    state = (
                        state.unswallowing(view)
                        .focusing_view(self._views[bv])
                        .without_view_state(view)
                        .constrain()
                    )

                    self.focus_borders.update_focus(
                        self._views[bv], present_states=(None, state)
                    )
                    self._views[bv].focus()

                except:
                    """
                    View might not exist anymore
                    """
                    state = (
                        state.unswallowing(view).without_view_state(view).constrain()
                    )

                    self.focus_borders.unfocus()

                return None, state

            self.animate_to(reducer, conf_anim_t())
        else:
            if view.is_focused():
                self.focus_borders.unfocus()
            self.animate_to(
                lambda state: (
                    None,
                    state.unswallowing(view).without_view_state(view).constrain(),
                ),
                conf_anim_t(),
            )

    def focus_hint(self, view: View) -> None:
        try:
            _, __, ws_handle = self.state.find_view(view)
            ws = [w for w in self.workspaces if w._handle == ws_handle][0]
            ws.focus_view_hint = view._handle

            ws_a, ws_a_old = self._active_workspace
            self._active_workspace = ws_a, ws

        except Exception:
            logger.warn("Missing state: %s" % self)

    def command(self, cmd: str, arg: Optional[str] = None) -> Optional[str]:
        logger.debug(f"Received command {cmd}")

        def set_inhibit_idle(status: bool) -> None:
            self._idle_inhibit_user = status

        def clean() -> None:
            def reducer(
                state: LayoutState,
            ) -> tuple[Optional[LayoutState], LayoutState]:
                new_state = state.copy().clean(list(self._views.keys()))
                return None, new_state

            self.animate_to(reducer, conf_anim_t())

        cmds: dict[str, Callable[[], Optional[str]]] = {
            "lock": lambda: self.ensure_locked(
                anim="anim" in arg if arg is not None else False,
                dim="dim" in arg if arg is not None else False,
            ),
            "config": print_config,
            "update-config": self.update_config,
            "debug": self.debug_str,
            "inhibit-idle": lambda: set_inhibit_idle(True),
            "finish-inhibit-idle": lambda: set_inhibit_idle(False),
            "close-launcher": lambda: self.exit_overlay()
            if isinstance(self.overlay, LauncherOverlay)
            else None,
            "open-virtual-output": lambda: self.open_virtual_output(arg)
            if arg is not None
            else None,
            "close-virtual-output": lambda: self.close_virtual_output(arg)
            if arg is not None
            else None,
            "clean": clean,
            "unlock": self._trusted_unlock
            if conf_enable_unlock_command()
            else lambda: "Disabled",
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

    def tiles(self, workspace: Optional[Workspace] = None) -> list[View]:
        return [
            v
            for _, v in self._views.items()
            if v.is_tiled(self.state) and self.is_view_on_workspace(v, workspace)
        ]

    def floats(self, workspace: Optional[Workspace] = None) -> list[View]:
        return [
            v
            for _, v in self._views.items()
            if v.is_float(self.state) and self.is_view_on_workspace(v, workspace)
        ]

    def panels(self, workspace: Optional[Workspace] = None) -> list[View]:
        return [
            v
            for _, v in self._views.items()
            if v.is_panel() and self.is_view_on_workspace(v, workspace)
        ]

    def views(self, workspace: Optional[Workspace] = None) -> list[View]:
        return [
            v
            for _, v in self._views.items()
            if not v.is_panel() and self.is_view_on_workspace(v, workspace)
        ]

    def find_focused_view(self) -> Optional[View]:
        for _, view in self._views.items():
            if view.is_focused():
                return view

        return None

    """
    2. General purpose methods
    """

    def update_config(self) -> None:
        load_config(fallback=False, path_str=self._config_file)
        self._setup()
        self.damage()

        conf_on_reconfigure()()

    def ensure_locked(self, anim: bool = True, dim: bool = False) -> None:
        def focus_lock() -> None:
            lock_screen = [v for v in self.panels() if v.panel == "lock"]
            if len(lock_screen) > 0:
                lock_screen[0].focus()
            else:
                logger.exception("Locking without lock panel - not a good idea")

        self.auth_backend.lock()

        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
            return None if anim else state.copy(
                lock_perc=1.0, background_opacity=0.5
            ), state.copy(lock_perc=1.0, background_opacity=0.5)

        self.animate_to(reducer, conf_anim_t(), focus_lock)

        if dim:
            conf_idle_callback()("lock")

    def terminate(self) -> None:
        def reducer(
            state: LayoutState,
        ) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            return state.copy(final=True), state.copy(
                final=True, background_opacity=0.0
            )

        self.animate_to(reducer, conf_blend_t(), self._terminate)

    """
    3. Change global or workspace state / move viewpoint
    """

    def enter_launcher_overlay(self) -> None:
        self.enter_overlay(LauncherOverlay(self))

    def toggle_overview(self, only_active_workspace: bool = False) -> None:
        def reducer(
            state: LayoutState,
        ) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            if only_active_workspace:
                overview = not state.get_workspace_state(
                    self.get_active_workspace()
                ).is_in_overview()
            else:
                overview = not state.all_in_overview()

            focused: Optional[View] = None
            if not overview:
                focused = self.find_focused_view()
            return None, state.with_overview_set(
                overview,
                None if not only_active_workspace else self.get_active_workspace(),
                focused,
            )

        self.animate_to(reducer, conf_anim_t())

    def toggle_fullscreen(self, defined_state: Optional[bool] = None) -> None:
        active_ws = self.get_active_workspace()

        def reducer(
            state: LayoutState,
        ) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            if state.get_workspace_state(self.get_active_workspace()).is_in_overview():
                state = state.with_overview_set(
                    False, only_workspace=self.get_active_workspace()
                )

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
                return None, state.setting_workspace_state(
                    ws, ws_state.without_fullscreen()
                )
            elif view is not None:
                return None, state.setting_workspace_state(
                    ws, ws_state.with_fullscreen(view)
                )
            else:
                return None, None

        self.animate_to(reducer, conf_anim_t())

    def basic_move(self, delta_i: int, delta_j: int) -> None:
        ws = self.get_active_workspace()

        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
            ws_state = state.get_workspace_state(ws)
            return None, state.replacing_workspace_state(
                ws, i=ws_state.i + delta_i, j=ws_state.j + delta_j
            )

        self.animate_to(reducer, conf_anim_t())

    def basic_scale(self, delta_s: int) -> None:
        ws = self.get_active_workspace()

        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
            ws_state = state.get_workspace_state(ws)
            return None, state.replacing_workspace_state(
                ws, size=max(1, ws_state.size + delta_s)
            )

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
            sid, idx, siz = view_state.stack_data
            nidx = (idx + 1) % siz
            next_view = [
                k
                for k, s in ws_state._view_states.items()
                if s.stack_data[0] == sid and s.stack_data[1] == nidx
            ]
            if len(next_view) > 0 and next_view[0] != view:
                self._views[next_view[0]].focus()
        except:
            logger.exception("Unexpected")

    def move(self, delta_i: int, delta_j: int) -> None:
        ws, i, j, w, h = self.find_focused_box()
        ws_state = self.state.get_workspace_state(ws)

        if (
            (i + w > ws_state.i + ws_state.size and delta_i > 0)
            or (i < ws_state.i and delta_i < 0)
            or (j + h > ws_state.j + ws_state.size and delta_j > 0)
            or (j < ws_state.j and delta_j < 0)
        ):
            vf = self.find_focused_view()
            if vf is not None:
                self.focus_view(vf)
                return

        best_view = None
        best_view_score = 1000.0

        for k, s in ws_state._view_states.items():
            if not s.is_tiled:
                continue

            sc = _score(i, j, w, h, delta_i, delta_j, s.i, s.j, s.w, s.h)
            if sc < best_view_score:
                best_view_score = sc
                best_view = k

        if best_view is not None:
            self.focus_view(self._views[best_view])

    def goto_view(
        self, index: int, active_workspace: bool = True, only_tiles: bool = False
    ) -> None:
        if index == 0:
            return
        workspace = self.get_active_workspace() if active_workspace else None
        views = self.tiles(workspace) if only_tiles else self.views(workspace)
        num_w = len(views)
        if index > num_w:
            return
        self.focus_view(views[index - 1])

    def cycle_views(
        self, steps: int = 1, active_workspace: bool = True, only_tiles: bool = False
    ) -> None:
        workspace = self.get_active_workspace() if active_workspace else None
        views = tuple(self.tiles(workspace) if only_tiles else self.views(workspace))
        current_view = self.find_focused_view()
        if not current_view or current_view not in views:
            return
        index = views.index(current_view) + steps
        self.__select_view(index, views)

    def __select_view(self, index: int, views: tuple[View, ...]) -> None:
        num_view = len(views)
        index = (index + num_view) % num_view
        self.focus_view(views[index])

    def move_workspace(self, ds: int = 1) -> None:
        ws = self.get_active_workspace()
        i, ws = [
            (i, w) for i, w in enumerate(self.workspaces) if w._handle == ws._handle
        ][0]

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
        def reducer(
            state: LayoutState,
        ) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            view = self.find_focused_view()
            if view is not None:
                try:
                    s, ws_state, ws_handle = state.find_view(view)
                    ws = [w for w in self.workspaces if w._handle == ws_handle][0]
                    s1, s2 = view.toggle_floating(s, ws, ws_state)

                    ws_state1 = ws_state.with_view_state(view, **s1.__dict__)
                    ws_state2 = ws_state.replacing_view_state(view, **s2.__dict__)
                    ws_state2.validate_stack_indices(view)

                    return (
                        state.setting_workspace_state(ws, ws_state1),
                        state.setting_workspace_state(ws, ws_state2),
                    )
                except:
                    return (None, state)
            else:
                return (None, state)

        self.animate_to(reducer, conf_anim_t())

    def change_focused_view_workspace(self, ds: int = 1) -> None:
        def reducer(
            state: LayoutState,
        ) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            view = self.find_focused_view()
            if view is not None:
                try:
                    s, ws_state, ws_handle = state.find_view(view)
                    i, ws = [
                        (i, w)
                        for i, w in enumerate(self.workspaces)
                        if w._handle == ws_handle
                    ][0]

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
        def reducer(
            state: LayoutState,
        ) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            view = self.find_focused_view()
            if view is not None:
                try:
                    s, ws_state, ws_handle = state.find_view(view)
                    ws = [w for w in self.workspaces if w._handle == ws_handle][0]
                    ws_state = ws_state.replacing_view_state(
                        view, i=s.i + di, j=s.j + dj
                    ).focusing_view(view)
                    ws_state.validate_stack_indices(view)
                    return (None, state.setting_workspace_state(ws, ws_state))
                except:
                    return (None, state)
            else:
                return (None, state)

        self.animate_to(reducer, conf_anim_t())

    def resize_focused_view(self, di: int, dj: int) -> None:
        def reducer(
            state: LayoutState,
        ) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
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
                    ws_state = ws_state.replacing_view_state(
                        view, i=i, j=j, w=w, h=h
                    ).focusing_view(view)
                    state.validate_stack_indices(view)
                    return (None, state.setting_workspace_state(ws, ws_state))
                except:
                    return (None, state)
            else:
                return (None, state)

        self.animate_to(reducer, conf_anim_t())

    def swallow_focused_view(self) -> None:
        def reducer(
            state: LayoutState,
        ) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            view = self.find_focused_view()
            if view is None:
                return None, None
            if not (view.is_tiled(state) or view.is_float(state)):
                return None, None

            by_view = view.find_swallower()
            if by_view is None:
                return None, None

            new_state = state.focusing_view(by_view)

            if view.is_tiled(state):
                by_state = state.get_view_state(by_view)
                new_state.update_view_state(
                    view,
                    swallowed=by_view._handle,
                    i=by_state.i,
                    j=by_state.j,
                    w=by_state.w,
                    h=by_state.h,
                )
            else:
                new_state.update_view_state(view, swallowed=by_view._handle)
            new_state.constrain()

            self.focus_borders.update_focus(by_view, present_states=(None, new_state))
            by_view.focus()

            return None, new_state

        self.animate_to(reducer, conf_anim_t())

    """
    6. Legacy
    """

    def close_view(self) -> None:
        self.close_focused_view()
