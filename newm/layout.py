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

from .state import LayoutState
from .interpolation import LayoutDownstreamInterpolation
from .animate import Animate
from .view import View
from .config import configured_value, load_config, print_config

from .key_processor import KeyProcessor
from .panel_endpoint import PanelEndpoint
from .panel_launcher import PanelsLauncher
from .sys_backend import SysBackend, SysBackendEndpoint
from .auth_backend import AuthBackend

from .widget import (
    TopBar,
    BottomBar,
    Background,
    Corner
)
from .overlay import (
    Overlay,
    MoveResizeOverlay,
    MoveResizeFloatingOverlay,
    SwipeOverlay,
    SwipeToZoomOverlay,
    LauncherOverlay,
    OverviewOverlay
)

logger = logging.getLogger(__name__)

conf_wallpaper = configured_value('wallpaper', cast(Optional[str], None))
conf_panel_dir = configured_value('panel_dir', cast(Optional[str], None))
conf_mod = configured_value('mod', PYWM_MOD_LOGO)
conf_pywm = configured_value('pywm', cast(dict[str, Any], {}))
conf_output_scale = configured_value('output_scale', 1.0)
conf_round_scale = configured_value('round_scale', 1.0)

conf_send_fullscreen_to_views = configured_value('view.send_fullscreen', True)

if TYPE_CHECKING:
    TKeyBindings = Callable[[Layout], list[tuple[str, Callable[[], None]]]]
else:
    TKeyBindings = TypeVar('TKeyBindings')

conf_key_bindings = configured_value('key_bindings', cast(TKeyBindings, lambda layout: []))
conf_sys_backend_endpoints = configured_value('sys_backend_endpoints', cast(list[SysBackendEndpoint], []))

conf_lp_freq = configured_value('gestures.lp_freq', 60.)
conf_lp_inertia = configured_value('gestures.lp_inertia', .8)
conf_two_finger_min_dist = configured_value('gestures.two_finger_min_dist', .1)
conf_validate_threshold = configured_value('gestures.validate_threshold', .02)

conf_anim_t = configured_value('anim_time', .3)
conf_blend_t = configured_value('blend_time', 1.)

conf_power_times = configured_value('power_times', [120, 300, 600])


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
    if j2 > j1 + h1:
        d_j = j2 - (j1 + h1)
    elif j1 > j2 + h2:
        d_j = j1 - (j2 + h2)

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
            """
            An animation may decide it does not want to be executed anymore
            """
            logger.debug("Animation decided not to take place")
            self._initial_state, self._final_state = None, None

        if self._initial_state is not None:
            self.layout.update(self._initial_state)

        self._started = time.time()
        if self._final_state is not None:
            # Enforce constraints on final state
            self._final_state.constrain()
            self._final_state.validate_fullscreen()

            self.layout._animate_to(self._final_state, self.duration)

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



class Layout(PyWM[View], Animate[PyWMDownstreamState]):
    def __init__(self) -> None:
        load_config()

        PyWM.__init__(self, View, output_scale=conf_output_scale(), round_scale=conf_round_scale(), **conf_pywm())
        Animate.__init__(self)

        self.mod = conf_mod()
        self.mod_sym = ""
        self._set_mod_sym()

        self.key_processor = KeyProcessor(self.mod_sym)
        self.sys_backend = SysBackend(self)
        self.auth_backend = AuthBackend(self)
        self.panel_launcher = PanelsLauncher()
        self.panel_endpoint = PanelEndpoint(self)

        self.state = LayoutState()

        self.overlay: Optional[Overlay] = None

        self.background: Optional[Background] = None
        self.top_bar: Optional[TopBar] = None
        self.bottom_bar: Optional[BottomBar] = None
        self.corners: list[Corner] = []

        self.thread = LayoutThread(self)

        self._animations: list[Animation] = []

        self._idle_inhibit_user = False


    def _set_mod_sym(self) -> None:
        self.mod_sym = ""
        if self.mod == PYWM_MOD_ALT:
            self.mod_sym = "Alt"
        elif self.mod == PYWM_MOD_LOGO:
            self.mod_sym = "Super"
        else:
            raise Exception("Unknown mod")

    def _setup(self, fallback: bool=True) -> None:
        load_config(fallback=fallback)

        self.round_scale = conf_round_scale()
        self.mod = conf_mod()
        self._set_mod_sym()

        self.configure_gestures(
            conf_two_finger_min_dist(),
            conf_lp_freq(),
            conf_lp_inertia(),
            conf_validate_threshold())

        if self.bottom_bar is not None:
            self.bottom_bar.stop()
            self.bottom_bar.destroy()
            self.bottom_bar = None

        if self.top_bar is not None:
            self.top_bar.stop()
            self.top_bar.destroy()
            self.top_bar = None

        if self.background is not None:
            self.background.destroy()
            self.background = None

        for c in self.corners:
            c.destroy()
        self.corners = []

        self.bottom_bar = self.create_widget(BottomBar)
        self.top_bar = self.create_widget(TopBar)
        if (wp := conf_wallpaper()) is not None:
            self.background = self.create_widget(Background, wp)
        self.corners = [
            self.create_widget(Corner, True, True),
            self.create_widget(Corner, True, False),
            self.create_widget(Corner, False, True),
            self.create_widget(Corner, False, False)
        ]

        self.key_processor.clear()
        if (kb := conf_key_bindings()) is not None:
            self.key_processor.register_bindings(
                *kb(self)
            )
        self.sys_backend.set_endpoints(
            *conf_sys_backend_endpoints()
        )
        self.sys_backend.register_xf86_keybindings()

    def reducer(self, state: LayoutState) -> PyWMDownstreamState:
        return PyWMDownstreamState(state.lock_perc)

    def animate(self, old_state: LayoutState, new_state: LayoutState, dt: float) -> None:
        cur = self.reducer(old_state)
        nxt = self.reducer(new_state)

        self._animate(LayoutDownstreamInterpolation(cur, nxt), dt)

    def process(self) -> PyWMDownstreamState:
        return self._process(self.reducer(self.state))

    def main(self) -> None:
        logger.debug("Layout main...")

        self._setup()

        self.thread.start()
        self.panel_endpoint.start()
        self.panel_launcher.start()

        # Initially display cursor
        self.update_cursor()

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

        if self.top_bar is not None:
            self.top_bar.stop()
        if self.bottom_bar is not None:
            self.bottom_bar.stop()
        if self.sys_backend is not None:
            self.sys_backend.stop()
        if self.thread is not None:
            self.thread.stop()

    def terminate(self) -> None:
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            return state.copy(final=True), state.copy(final=True, background_opacity=0.)
        self.animate_to(reducer, conf_blend_t(), self._terminate)


    def _execute_view_main(self, view: View) -> None:
        self.animate_to(view.main, conf_anim_t(), None)


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

        if self.background is not None:
            self.background.damage()

        if self.top_bar is not None:
            self.top_bar.damage()

        if self.bottom_bar is not None:
            self.bottom_bar.damage()


    def update(self, new_state: LayoutState) -> None:
        self.state = new_state
        self.damage()

    def _animate_to(self, new_state: LayoutState, duration: float) -> None:
        self.animate(self.state, new_state, duration)

        for _, v in self._views.items():
            v.animate(self.state, new_state, duration)

        if self.background is not None:
            self.background.animate(self.state, new_state, duration)

        if self.top_bar is not None:
            self.top_bar.animate(self.state, new_state, duration)

        if self.bottom_bar is not None:
            self.bottom_bar.animate(self.state, new_state, duration)



    """
    Utilities
    """

    def __str__(self) -> str:
        return "<Layout %dx%d %s>" % (self.width, self.height, self.config)

    def debug_str(self) -> str:
        res = "%s\n  %s\n\n" % (self, str(self.state))
        for i, v in self._views.items():
            s = None
            try:
                s = self.state.get_view_state(v)
            except:
                pass
            res += "%2d: %s\n      %s\n" % (i, v, s)
        return res

    def windows(self) -> list[View]:
        return [v for _, v in self._views.items() if v.is_window()]

    def dialogs(self) -> list[View]:
        return [v for _, v in self._views.items() if v.is_dialog()]

    def panels(self) -> list[View]:
        return [v for _, v in self._views.items() if v.is_panel()]

    def find_focused_box(self) -> tuple[float, float, float, float]:
        try:
            view = self.find_focused_view()
            if view is not None:
                view_state = self.state.get_view_state(view)
            return view_state.i, view_state.j, view_state.w, view_state.h
        except Exception:
            return 0, 0, 1, 1

    def find_focused_view(self) -> Optional[View]:
        for _, view in self._views.items():
            if view.is_focused():
                return view

        return None

    def place_initial(self, w: int, h: int) -> tuple[int, int]:
        place_i = 0
        place_j = 0

        i, j = self.state.i, self.state.j
        # Special case of centered window if extent < size
        i, j = math.ceil(i), math.ceil(j)
        for j, i in product(range(math.floor(j),
                                  math.ceil(j + self.state.size)),
                            range(math.floor(i),
                                  math.ceil(i + self.state.size))):
            for jp, ip in product(range(j, j + h), range(i, i + w)):
                if not self.state.is_tile_free(ip, jp):
                    break
            else:
                place_i, place_j = i, j
                break
        else:
            i_, j_, w_, h_ = self.find_focused_box()
            place_i, place_j = round(i_ + w_), round(j_)
            while not self.state.is_tile_free(place_i, place_j):
                place_i += 1

        logger.debug("Found initial placement at %d, %d (state = %f, %f, %f)", place_i, place_j, self.state.i, self.state.j, self.state.size)
        return place_i, place_j


    """
    Callbacks
    """

    def on_layout_change(self) -> None:
        self._setup()

    def on_key(self, time_msec: int, keycode: int, state: int, keysyms: str) -> bool:
        if self.is_locked():
            return False

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
                                         self.modifiers & self.mod > 0,
                                         self.modifiers & PYWM_MOD_CTRL > 0)

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
                if view is not None and view.is_dialog():
                    ovr = MoveResizeFloatingOverlay(self, view)
                    ovr.on_gesture(gesture)
                    self.enter_overlay(ovr)
                    return True

                elif view is not None and view.is_window():
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


    """
    Actions
    """

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
            self.sys_backend.idle_state(1)

    def _trusted_unlock(self) -> None:
        if self.is_locked():
            def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
                return None, state.copy(lock_perc=0., background_opacity=1.)
            self.animate_to(
                reducer,
                conf_anim_t(),
                lambda: self.update_cursor())

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

    def move(self, delta_i: int, delta_j: int) -> None:
        i, j, w, h = self.find_focused_box()

        if ((i + w > self.state.i + self.state.size and delta_i > 0) or
                (i < self.state.i and delta_i < 0) or
                (j + h > self.state.j + self.state.size and delta_j > 0) or
                (j < self.state.j and delta_j < 0)):

            vf = self.find_focused_view()
            if vf is not None:
                self.focus_view(vf)
                return


        best_view = None
        best_view_score = 1000.

        for k, s in self.state._view_states.items():
            if not s.is_tiled:
                continue

            sc = _score(i, j, w, h, delta_i, delta_j, s.i, s.j, s.w, s.h)
            if sc < best_view_score:
                best_view_score = sc
                best_view = k

        if best_view is not None:
            self.focus_view(self._views[best_view])


    def close_view(self) -> None:
        view = [v for _, v in self._views.items() if v.is_focused()]
        if len(view) == 0:
            return

        view[0].close()


    def focus_view(self, view: View) -> None:
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
            view.focus()
            return None, state.focusing_view(view)
        self.animate_to(reducer, conf_anim_t())

    def destroy_view(self, view: View) -> None:
        logger.info("Destroying view %s", view)
        state = None
        try:
            state = self.state.get_view_state(view)
        except:
            logger.warn("Unexpected: View %s state not found", view)
            return

        best_view: Optional[int] = None
        best_view_score = 1000.
        if view.is_focused():
            logger.debug("Finding view to focus since %s (%d) closes...", view.app_id, view._handle)
            for k, s in self.state._view_states.items():
                if not s.is_tiled:
                    continue

                if k == view._handle:
                    continue

                sc = (s.i - state.i + s.w / 2. - state.w / 2.)**2 + (s.j - state.j + s.h / 2. - state.h / 2.)**2
                logger.debug("View (%d) has score %f", k, sc)
                if sc < best_view_score:
                    best_view_score = sc
                    best_view = k

        if best_view is not None and best_view in self._views:
            bv: int = best_view
            def reducer(state: LayoutState) -> tuple[Optional[LayoutState], LayoutState]:
                self._views[bv].focus()
                return None, state\
                    .focusing_view(self._views[bv])\
                    .without_view_state(view)

            self.animate_to(
                reducer,
                conf_anim_t())
        else:
            self.animate_to(
                lambda state: (None, state
                    .copy()
                    .without_view_state(view)),
                conf_anim_t())


    def toggle_fullscreen(self) -> None:
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            view = self.find_focused_view()
            fs = state.is_fullscreen()

            if conf_send_fullscreen_to_views():
                for v in self.windows():
                    v.set_fullscreen(not fs)

            if fs:
                return None, state.without_fullscreen()
            elif view is not None:
                return None, state.with_fullscreen(view)
            else:
                return None, None
        self.animate_to(reducer, conf_anim_t())

    def move_focused_view(self, di: int, dj: int) -> None:
        def reducer(state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
            view = self.find_focused_view()
            if view is not None:
                try:
                    s = state.get_view_state(view)
                    return (None, state.replacing_view_state(view, i=s.i+di, j=s.j+dj).focusing_view(view))
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
                    return (None, state.replacing_view_state(view, i=i, j=j, w=w, h=h).focusing_view(view))
                except:
                    return (None, state)
            else:
                return (None, state)
        self.animate_to(reducer, conf_anim_t())

    def update_config(self) -> None:
        self._setup(fallback=False)
        self.damage()

    def enter_overview_overlay(self) -> None:
        self.enter_overlay(OverviewOverlay(self))

    def enter_launcher_overlay(self) -> None:
        self.enter_overlay(LauncherOverlay(self))

    def command(self, cmd: str) -> Optional[str]:
        logger.debug("Received command %s", cmd)
        if cmd == "anim-lock":
            self.ensure_locked()
        elif cmd == "lock":
            self.ensure_locked()
        elif cmd == "lock-pre":
            self.ensure_locked(anim=False)
        elif cmd == "lock-post":
            self._update_idle(True)
            self.ensure_locked(anim=False)
        elif cmd == "config":
            return print_config()
        elif cmd == "debug":
            return self.debug_str()
        elif cmd == "inhibit-idle":
            self._idle_inhibit_user = True
        elif cmd == "finish-inhibit-idle":
            self._idle_inhibit_user = False

        return None

    def launch_app(self, cmd: str) -> None:
        """
        Should be LauncherOverlay
        """
        self.exit_overlay()
        os.system("%s &" % cmd)

    def on_idle(self, elapsed: float, idle_inhibited: bool) -> None:
        idle_inhibited = idle_inhibited or self._idle_inhibit_user

        if idle_inhibited and elapsed > 0:
            return

        if elapsed == 0:
            self.sys_backend.idle_state(0)
        elif len(conf_power_times()) > 2 and elapsed > conf_power_times()[2]:
            # TODO - this command (no matter from where it's executed does not work at the moment)
            os.system("systemctl suspend")
        elif len(conf_power_times()) > 1 and elapsed > conf_power_times()[1]:
            self.sys_backend.idle_state(2)
            self.ensure_locked()
        elif len(conf_power_times()) > 0 and elapsed > conf_power_times()[0]:
            self.sys_backend.idle_state(1)
