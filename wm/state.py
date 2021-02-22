import math

DEFAULT_PADDING = 0.01

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



class LayoutState:
    def __init__(self, **kwargs):

        self.i = kwargs['i'] if 'i' in kwargs else 0
        self.j = kwargs['j'] if 'j' in kwargs else 0
        self.size = kwargs['size'] if 'size' in kwargs else 2
        self.scale = kwargs['scale'] if 'scale' in kwargs else 2

        self.padding = kwargs['padding'] if 'padding' in kwargs else DEFAULT_PADDING

        self.background_factor = kwargs['background_factor'] if 'background_factor' in kwargs else 3

        self.top_bar_dy = kwargs['top_bar_dy'] if 'top_bar_dy' in kwargs else 0
        self.bottom_bar_dy = kwargs['bottom_bar_dy'] if 'bottom_bar_dy' in kwargs else 0

        self.launcher_perc = kwargs['launcher_perc'] if 'launcher_perc' in kwargs else 0

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
            print("Unable to update view state: %s" % view)

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

        target_scale = target_size
        target_padding = self.padding

        if target_i != self.i or target_j != self.j or target_size != self.size:
            if target_padding == 0:
                target_padding = DEFAULT_PADDING

        return self.copy(
            i=target_i,
            j=target_j,
            size=target_size,
            scale=target_scale,
            padding=target_padding
        )

    def with_padding_toggled(self, focus_box=(0, 0, 1, 1), reset=None):
        padding = DEFAULT_PADDING if self.padding == 0 else 0

        if padding == 0:
            new_i = focus_box[0]
            new_j = focus_box[1]
            new_size = max(focus_box[2:])
            new_scale = int(new_size / self.size * self.scale)

            return self.copy(
                padding=padding,
                i=new_i,
                j=new_j,
                size=new_size,
                scale=new_scale)

        else:
            new_i = self.i
            new_j = self.j
            new_size = self.size

            if reset is not None:
                new_i=reset[0]
                new_j=reset[1]
                new_size=reset[2]

            new_scale = int(new_size / self.size * self.scale)

            return self.copy(
                padding=padding,
                i=new_i,
                j=new_j,
                size=new_size,
                scale=new_scale
            )


    """
    Access information
    """

    def __str__(self):
        return "LayoutState <%s>" % str(self.__dict__)

    def get_view_state(self, view):
        return self._view_states[view._handle]

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

            if math.floor(s.i) <= i and math.ceil(s.i + s.w - 1) >= i \
                    and math.floor(s.j) <= j and math.ceil(s.j + s.h - 1) >= j:
                return False

        return True

