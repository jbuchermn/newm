import math
import logging

from .config import configured_value

logger = logging.getLogger(__name__)



class ViewState:
    def __init__(self, **kwargs):
        self.is_tiled = kwargs['is_tiled'] if 'is_tiled' in kwargs else True

        self.i = kwargs['i'] if 'i' in kwargs else 0
        self.j = kwargs['j'] if 'j' in kwargs else 0
        self.w = kwargs['w'] if 'w' in kwargs else 0
        self.h = kwargs['h'] if 'h' in kwargs else 0

        """
        MoveResizeOverlay
        """
        self.move_origin = kwargs['move_origin'] if 'move_origin' in kwargs \
            else (None, None)
        self.scale_origin = kwargs['scale_origin'] if 'scale_origin' in kwargs \
            else (None, None)

    def copy(self, **kwargs):
        return ViewState(**{**self.__dict__, **kwargs})

    def update(self, **kwargs):
        for k, v in kwargs.items():
            self.__dict__[k] = v

    def __str__(self):
        return "ViewState <%s>" % str(self.__dict__)

    def __repr__(self):
        return str(self)



class LayoutState:
    def __init__(self, **kwargs):

        self.i = kwargs['i'] if 'i' in kwargs else 0
        self.j = kwargs['j'] if 'j' in kwargs else 0
        self.size = kwargs['size'] if 'size' in kwargs else 2
        self.scale = kwargs['scale'] if 'scale' in kwargs else 1

        self.background_factor = kwargs['background_factor'] if 'background_factor' in kwargs else 3
        self.background_opacity = kwargs['background_opacity'] if 'background_opacity' in kwargs else 0.

        self.intermediate_rows = kwargs['intermediate_rows'] if 'intermediate_rows' in kwargs else []
        self.intermediate_cols = kwargs['intermediate_cols'] if 'intermediate_cols' in kwargs else []
        # Non-None indicates fullscreen, in that case i, j, size
        self.state_before_fullscreen = kwargs['state_before_fullscreen'] if 'state_before_fullscreen' in kwargs else None

        self.top_bar_dy = kwargs['top_bar_dy'] if 'top_bar_dy' in kwargs else 0
        self.bottom_bar_dy = kwargs['bottom_bar_dy'] if 'bottom_bar_dy' in kwargs else 0
        self.launcher_perc = kwargs['launcher_perc'] if 'launcher_perc' in kwargs else 0
        self.lock_perc = kwargs['lock_perc'] if 'lock_perc' in kwargs else 0
        self.final = kwargs['final'] if 'final' in kwargs else False

        self._view_states = {}

    """
    Register / Unregister
    """

    def with_view_state(self, view, **kwargs):
        self._view_states[view._handle] = ViewState(**kwargs)
        return self


    def without_view_state(self, view):
        del self._view_states[view._handle]
        return self

    """
    Copy / Update
    """

    def copy(self, **kwargs):
        res = LayoutState(**{**self.__dict__, **kwargs})
        for h, s in self._view_states.items():
            res._view_states[h] = s.copy()
        return res

    def update(self, **kwargs):
        for k, v in kwargs.items():
            self.__dict__[k] = v

    def replacing_view_state(self, view, **kwargs):
        res = LayoutState(**self.__dict__)
        for h, s in self._view_states.items():
            res._view_states[h] = s.copy(**(kwargs if h==view._handle else {}))
        return res

    def update_view_state(self, view, **kwargs):
        try:
            s = self.get_view_state(view)
            s.update(**kwargs)
        except Exception:
            logger.warn("Unexpected: Unable to update view %s state", view)

    def constrain(self):
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


    def _insert_intermediate_col(self, i):
        for _, s in self._view_states.items():
            if s.i >= i:
                s.i += 1
            elif s.i + s.w - 1 >= i:
                s.w += 1
        self.intermediate_cols += [i]


    def _insert_intermediate_row(self, j):
        for _, s in self._view_states.items():
            if s.j >= j:
                s.j += 1
            elif s.j + s.h - 1 >= j:
                s.h += 1
        self.intermediate_rows += [j]

    def _clear_intermediate(self):
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

    def focusing_view(self, view):
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

    def with_fullscreen(self, view):
        state = self.get_view_state(view)
        i, j, w, h = state.i, state.j, state.w, state.h
        size = max(w, h)

        state_before_fullscreen = self.i, self.j, self.size

        result = self.copy(state_before_fullscreen=state_before_fullscreen, i=i, j=j, size=size)

        for ii in range(w, size):
            result._insert_intermediate_col(i + ii)

        for jj in range(h, size):
            result._insert_intermediate_col(j + jj)

        result.update_view_state(view, w=size, h=size)

        return result

    def without_fullscreen(self, drop=False):
        if self.state_before_fullscreen is None:
            return self.copy()

        if drop:
            i, j, size = self.i, self.j, self.size
        else:
            i, j, size = self.state_before_fullscreen

            # Possibly invalidate state_before_fullscreen
            if self.i < i or self.i > i + size - 1:
                i, j = self.i, self.j
            if self.j < j or self.j > j + size - 1:
                i, j = self.i, self.j

        result = self.copy(state_before_fullscreen=None, i=i, j=j, size=size)
        result._clear_intermediate()
        return result


    """
    Access information
    """

    def __str__(self):
        return "LayoutState <%s>" % str(self.__dict__)

    def __repr__(self):
        return str(self)

    def get_view_state(self, view):
        return self._view_states[view._handle]

    def get_view_stack_index(self, view):
        vs = self.get_view_state(view)
        relevant = []

        i, j, w, h = vs.i, vs.j, vs.w, vs.h
        if vs.scale_origin[0] is not None:
            w, h = vs.scale_origin
        if vs.move_origin[0] is not None:
            i, j = vs.move_origin

        for handle, s in self._view_states.items():
            if not s.is_tiled:
                continue

            i_, j_, w_, h_ = s.i, s.j, s.w, s.h
            if s.scale_origin[0] is not None:
                w_, h_ = s.scale_origin
            if s.move_origin[0] is not None:
                i_, j_ = s.move_origin

            if not ((i_ <= i < i_ + w_ - .2) or (i <= i_ < i + w - .2)):
                continue
            if not ((j_ <= j < j_ + h_ - .2) or (j <= j_ < j + h - .2)):
                continue

            relevant += [handle]

        if view._handle not in relevant:
            # In case of w or h == 0 this may happen
            return 0, 1

        relevant = sorted(relevant)
        return relevant.index(view._handle), len(relevant)

    def get_extent(self):
        min_i, min_j, max_i, max_j = 1000000, 1000000, -1000000, -1000000

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

    def is_tile_free(self, i, j):
        for _, s in self._view_states.items():
            if not s.is_tiled:
                continue

            if math.floor(s.i) <= i <= math.ceil(s.i + s.w - 1) \
                    and math.floor(s.j) <= j <= math.ceil(s.j + s.h - 1):
                return False

        return True

    def is_fullscreen(self):
        return self.state_before_fullscreen is not None
