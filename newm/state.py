from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING

import math
import logging

if TYPE_CHECKING:
    from .view import View

logger = logging.getLogger(__name__)

class ViewState:
    def __init__(self, **kwargs: Any) -> None:
        self.is_tiled: bool = kwargs['is_tiled'] if 'is_tiled' in kwargs else True

        self.i: float = kwargs['i'] if 'i' in kwargs else 0
        self.j: float = kwargs['j'] if 'j' in kwargs else 0
        self.w: float = kwargs['w'] if 'w' in kwargs else 0
        self.h: float = kwargs['h'] if 'h' in kwargs else 0

        """
        MoveResizeOverlay
        """
        self.move_origin: tuple[Optional[float], Optional[float]] = kwargs['move_origin'] if 'move_origin' in kwargs \
            else (None, None)
        self.scale_origin: tuple[Optional[float], Optional[float]] = kwargs['scale_origin'] if 'scale_origin' in kwargs \
            else (None, None)

        """
        stack_id / idx / len
        """
        self.stack_data: tuple[int, int, int] = kwargs['stack_data'] if 'stack_data' in kwargs else (-1, 0, 1)

        """
        Global stack_idx (Compare z-index) to restore ordering
        """
        self.stack_idx: int = kwargs['stack_idx'] if 'stack_idx' in kwargs else 0

    def get_ijwh(self) -> tuple[float, float, float, float]:
        i, j, w, h = self.i, self.j, self.w, self.h
        if self.move_origin[0] is not None:
            i = self.move_origin[0]
        if self.move_origin[1] is not None:
            j = self.move_origin[1]
        if self.scale_origin[0] is not None:
            w = self.scale_origin[0]
        if self.scale_origin[1] is not None:
            h = self.scale_origin[1]

        return i, j, w, h

    def copy(self, **kwargs: Any) -> ViewState:
        return ViewState(**{**self.__dict__, **kwargs})

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            self.__dict__[k] = v

    def __str__(self) -> str:
        return "<ViewState %s>" % str(self.__dict__)

    def __repr__(self) -> str:
        return str(self)



class LayoutState:
    def __init__(self, **kwargs: Any) -> None:

        self.i: float = kwargs['i'] if 'i' in kwargs else 0
        self.j: float = kwargs['j'] if 'j' in kwargs else 0
        self.size: float = kwargs['size'] if 'size' in kwargs else 2
        self.size_origin: Optional[float] = kwargs['size_origin'] if 'size_origin' in kwargs else None

        self.background_factor: float = kwargs['background_factor'] if 'background_factor' in kwargs else 3
        self.background_opacity: float = kwargs['background_opacity'] if 'background_opacity' in kwargs else 0.

        self.intermediate_rows: list[int] = kwargs['intermediate_rows'] if 'intermediate_rows' in kwargs else []
        self.intermediate_cols: list[int] = kwargs['intermediate_cols'] if 'intermediate_cols' in kwargs else []
        # Non-None indicates fullscreen, in that case i, j, size, i in fullscreen, j in fullscreen, size in fullscreen
        self.state_before_fullscreen: Optional[tuple[float, float, float, float, float, float]] = kwargs['state_before_fullscreen'] if 'state_before_fullscreen' in kwargs else None

        self.top_bar_dy: float = kwargs['top_bar_dy'] if 'top_bar_dy' in kwargs else 0
        self.bottom_bar_dy: float = kwargs['bottom_bar_dy'] if 'bottom_bar_dy' in kwargs else 0
        self.launcher_perc: float = kwargs['launcher_perc'] if 'launcher_perc' in kwargs else 0
        self.lock_perc: float = kwargs['lock_perc'] if 'lock_perc' in kwargs else 0
        self.final: bool = kwargs['final'] if 'final' in kwargs else False

        # Non-null indicates we are in overview mode, in that case i, j, size, size_origin, background_factor, top_bar_dy, bottom_bar_dy
        self.state_before_overview: Optional[tuple[float, float, float, Optional[float], float, float, float]] = kwargs['state_before_overview'] if 'state_before_overview' in kwargs else None

        self._view_states: dict[int, ViewState] = {}

    """
    Register / Unregister
    """

    def with_view_state(self, view: View, **kwargs: Any) -> LayoutState:
        self._view_states[view._handle] = ViewState(**kwargs)
        return self


    def without_view_state(self, view: View) -> LayoutState:
        del self._view_states[view._handle]
        return self

    """
    Copy / Update
    """

    def copy(self, **kwargs: Any) -> LayoutState:
        res = LayoutState(**{**self.__dict__, **kwargs})
        for h, s in self._view_states.items():
            res._view_states[h] = s.copy()
        return res

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            self.__dict__[k] = v

    def replacing_view_state(self, view: View, **kwargs: Any) -> LayoutState:
        res = LayoutState(**self.__dict__)
        for h, s in self._view_states.items():
            res._view_states[h] = s.copy(**(kwargs if h==view._handle else {}))
        return res

    def update_view_state(self, view: View, **kwargs: Any) -> None:
        try:
            s = self.get_view_state(view)
            s.update(**kwargs)
        except Exception:
            logger.warn("Unexpected: Unable to update view %s state", view)


    def validate_fullscreen(self) -> None:
        if self.state_before_fullscreen is not None:
            _1, _2, _3, i, j, size = self.state_before_fullscreen
            if abs(self.i - i) + abs(self.j - j) + abs(self.size - size) > .01:
                self.state_before_fullscreen = None

    def validate_stack_indices(self, moved_view: Optional[View]=None) -> None:
        """
        Set stack_data = idx, len for every view according to as-is placement
        Place moved_view on top of stack if it is set (and set stack_idx analogously)
        """

        def overlaps(s1: ViewState, s2: ViewState) -> bool:
            i, j, w, h = s1.get_ijwh()
            i_, j_, w_, h_ = s2.get_ijwh()
            if not ((i_ - .2 <= i < i_ + w_ - .8) or (i - .2 <= i_ < i + w - .8)):
                return False
            if not ((j_ - .2 <= j < j_ + h_ - .8) or (j - .2 <= j_ < j + h - .8)):
                return False
            return True

        def stacks_overlap(s1: list[tuple[int, ViewState]], s2: list[tuple[int, ViewState]]) -> bool:
            for v, s in s1:
                for vp, sp in s2:
                    if overlaps(s, sp):
                        return True
            return False

        stacks: list[list[tuple[int, ViewState]]] = [[(v, s)] for v, s in self._view_states.items() if s.is_tiled]
        change = True
        while change:
            change = False
            for i in range(len(stacks)):
                for j in range(i):
                    if stacks_overlap(stacks[i], stacks[j]):
                        stacks[i] += stacks[j]
                        del stacks[j]
                        change = True
                        break
                if change:
                    break

        for s_id, stack in enumerate(stacks):
            def key(a: tuple[int, ViewState]) -> int:
                return a[1].stack_idx

            if moved_view is not None:
                for v, s in stack:
                    if v == moved_view._handle:
                        max_idx = max([key(a) for a in stack])
                        if s.stack_idx < max_idx:
                            s.stack_idx = max_idx + 1
                        break

            s_stack = sorted(stack, key=key)
            for i, (v, s) in enumerate(s_stack):
                s.stack_data = s_id, i, len(s_stack)

            """
            Occasionally reset stack_idx
            """
            if len(stack) == 1:
                stack[0][1].stack_idx = stack[0][0]


    def constrain(self) -> None:
        min_i, min_j, max_i, max_j = self.get_extent()
        i_size = max_i - min_i + 1
        j_size = max_j - min_j + 1

        if self.size > i_size:
            self.i = min_i + .5*i_size - .5*self.size
        else:
            if self.i < min_i:
                self.i = min_i
            if self.i + self.size - 1 > max_i:
                self.i = max_i - self.size + 1
        if self.size > j_size:
            self.j = min_j + .5*j_size - .5*self.size
        else:
            if self.j < min_j:
                self.j = min_j
            if self.j + self.size - 1 > max_j:
                self.j = max_j - self.size + 1

        used_rows = set()
        used_cols = set()
        for _, s in self._view_states.items():
            if not s.is_tiled:
                continue

            i_, j_, w_, h_ = [round(a) for a in s.get_ijwh()]

            for i in range(i_, i_ + w_):
                used_cols.add(i)
            for j in range(j_, j_ + h_):
                used_rows.add(j)

        cols = list(sorted(used_cols))
        rows = list(sorted(used_rows))
        remove_cols = []
        remove_rows = []
        for i in range(len(cols) - 1):
            for x in range(cols[i] + 1, cols[i+1]):
                remove_cols += [x]
        for i in range(len(rows) - 1):
            for x in range(rows[i] + 1, rows[i+1]):
                remove_rows += [x]

        for j in reversed(remove_rows):
            for _, s in self._view_states.items():
                if s.j >= j:
                    s.j -= 1
                elif s.j + s.h - 1 >= j:
                    s.h = max(1, s.h - 1)
        for i in reversed(remove_cols):
            for _, s in self._view_states.items():
                if s.i >= i:
                    s.i -= 1
                elif s.i + s.w - 1 >= i:
                    s.w = max(1, s.w - 1)


    def _insert_intermediate_col(self, i: int) -> None:
        for _, s in self._view_states.items():
            if s.i >= i:
                s.i += 1
            elif s.i + s.w - 1 >= i:
                s.w += 1
        self.intermediate_cols += [i]


    def _insert_intermediate_row(self, j: int) -> None:
        for _, s in self._view_states.items():
            if s.j >= j:
                s.j += 1
            elif s.j + s.h - 1 >= j:
                s.h += 1
        self.intermediate_rows += [j]

    def _clear_intermediate(self) -> None:
        for j in reversed(sorted(self.intermediate_rows)):
            for _, s in self._view_states.items():
                if s.j >= j:
                    s.j -= 1
                elif s.j + s.h - 1 >= j:
                    s.h = max(1, s.h - 1)
        for i in reversed(sorted(self.intermediate_cols)):
            for _, s in self._view_states.items():
                if s.i >= i:
                    s.i -= 1
                elif s.i + s.w - 1 >= i:
                    s.w = max(1, s.w - 1)
        self.intermediate_rows = []
        self.intermediate_cols = []

    """
    Reducers
    """

    def focusing_view(self, view: View) -> LayoutState:
        state = self._view_states[view._handle]

        i, j, w, h = state.i, state.j, state.w, state.h
        target_i, target_j, target_size = self.i, self.j, self.size

        target_size = max(target_size, w, h)
        target_i = min(target_i, i)
        target_j = min(target_j, j)
        target_i = max(target_i, i + w - target_size)
        target_j = max(target_j, j + h - target_size)

        return self.copy(
            i=target_i,
            j=target_j,
            size=target_size,
        )

    def with_fullscreen(self, view: View) -> LayoutState:
        state = self.get_view_state(view)
        i_, j_, w_, h_ = state.i, state.j, state.w, state.h
        i, j, w, h = round(i_), round(j_), round(w_), round(h_)
        size = max(w, h)

        state_before_fullscreen = self.i, self.j, self.size, i, j, size

        result = self.copy(state_before_fullscreen=state_before_fullscreen, i=i, j=j, size=size)

        for ii in range(w, size):
            result._insert_intermediate_col(i + ii)

        for jj in range(h, size):
            result._insert_intermediate_row(j + jj)

        result.update_view_state(view, w=size, h=size)

        return result

    def without_fullscreen(self, drop: bool=False) -> LayoutState:
        if self.state_before_fullscreen is None:
            return self.copy()

        if drop:
            i, j, size = self.i, self.j, self.size
        else:
            i, j, size, _1, _2, _3 = self.state_before_fullscreen

            # Possibly invalidate state_before_fullscreen
            if self.i < i or self.i > i + size - 1:
                i, j = self.i, self.j
            if self.j < j or self.j > j + size - 1:
                i, j = self.i, self.j

        result = self.copy(state_before_fullscreen=None, i=i, j=j, size=size)
        result._clear_intermediate()
        return result

    def with_overview_toggled(self, view: Optional[View]=None) -> LayoutState:
        if self.state_before_overview is None:
            min_i, min_j, max_i, max_j = self.get_extent()

            width = max_i - min_i + 3
            height = max_j - min_j + 3
            size = max(width, height)
            i = min_i - (size - (max_i - min_i + 1)) / 2.
            j = min_j - (size - (max_j - min_j + 1)) / 2.

            state_before_overview = self.i, self.j, self.size, self.size_origin, self.background_factor, self.top_bar_dy, self.bottom_bar_dy
            return self.copy(
                i=i,
                j=j,
                size=size,
                size_origin=self.size,
                background_factor=1.,
                top_bar_dy=1.,
                bottom_bar_dy=1.,
                state_before_overview=state_before_overview
            )
        else:
            i, j, size, size_origin, background_factor, top_bar_dy, bottom_bar_dy = self.state_before_overview
            state = self.copy(
                i=i,
                j=j,
                size=size,
                size_origin=size_origin,
                background_factor=background_factor,
                top_bar_dy=top_bar_dy,
                bottom_bar_dy=bottom_bar_dy,
                state_before_overview=None
            )
            if view is not None:
                state = state.focusing_view(view)
            return state


    """
    Access information
    """

    def __str__(self) -> str:
        return "<LayoutState %s>" % str({k:v for k, v in self.__dict__.items() if k != "_view_states"})

    def __repr__(self) -> str:
        return str(self)

    def get_view_state(self, view: View) -> ViewState:
        return self._view_states[view._handle]


    def get_extent(self) -> tuple[float, float, float, float]:
        min_i, min_j, max_i, max_j = 1000000., 1000000., -1000000., -1000000.

        for _, s in self._view_states.items():
            if not s.is_tiled:
                continue
            if s.w == 0 or s.h == 0:
                continue

            i, j = s.i, s.j
            w, h = s.w, s.h

            min_i = min(min_i, i)
            min_j = min(min_j, j)
            max_i = max(max_i, i + w - 1)
            max_j = max(max_j, j + h - 1)

        if min_i == 1000000:
            return 0, 0, 0, 0

        return min_i, min_j, max_i, max_j

    def is_tile_free(self, i: int, j: int) -> bool:
        for _, s in self._view_states.items():
            if not s.is_tiled:
                continue

            if math.floor(s.i) <= i <= math.ceil(s.i + s.w - 1) \
                    and math.floor(s.j) <= j <= math.ceil(s.j + s.h - 1):
                return False

        return True

    def is_fullscreen(self) -> bool:
        return self.state_before_fullscreen is not None

    def is_in_overview(self) -> bool:
        return self.state_before_overview is not None
