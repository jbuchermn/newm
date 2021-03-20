from pywm import PyWMViewDownstreamState, PyWMWidgetDownstreamState, PyWMDownstreamState

from .config import configured_value

conf_size_adjustment = configured_value("interpolation.size_adjustment", .5)

class LayoutDownstreamInterpolation:
    def __init__(self, state0, state1):
        self.lock_perc = (state0.lock_perc, state1.lock_perc)

    def get(self, at):
        at = min(1, max(0, at))
        lock_perc=self.lock_perc[0] + at * (self.lock_perc[1] - self.lock_perc[0])
        if lock_perc < 0.0001:
            lock_perc = 0.0
        return PyWMDownstreamState(lock_perc)

class ViewDownstreamInterpolation:
    def __init__(self, state0, state1):
        self.z_index = (state0.z_index, state1.z_index)
        self.box = (state0.box, state1.box)
        self.corner_radius = (state0.corner_radius, state1.corner_radius)
        self.accepts_input = state1.accepts_input
        self.size = (state0.size, state1.size)
        self.opacity = (state0.opacity, state1.opacity)
        self.lock_enabled = state0.lock_enabled

    def get(self, at):
        at = min(1, max(0, at))
        box=(
            self.box[0][0] + (self.box[1][0] - self.box[0][0]) * at,
            self.box[0][1] + (self.box[1][1] - self.box[0][1]) * at,
            self.box[0][2] + (self.box[1][2] - self.box[0][2]) * at,
            self.box[0][3] + (self.box[1][3] - self.box[0][3]) * at,
        )
        res = PyWMViewDownstreamState(
            z_index=self.z_index[1] if at > 0.5 else self.z_index[0],
            box=box,
            corner_radius=(self.corner_radius[0] + at * (self.corner_radius[1] - self.corner_radius[0])),
            accepts_input=self.accepts_input
        )

        res.opacity = self.opacity[0] + at * (self.opacity[1] - self.opacity[0])
        res.size=self.size[1] if at > conf_size_adjustment() else self.size[0]
        res.lock_enabled=self.lock_enabled
        return res

class WidgetDownstreamInterpolation:
    def __init__(self, state0, state1):
        self.z_index = (state0.z_index, state1.z_index)
        self.box = (state0.box, state1.box)
        self.opacity = (state0.opacity, state1.opacity)
        self.lock_enabled = state0.lock_enabled

    def get(self, at):
        at = min(1, max(0, at))
        box=(
            self.box[0][0] + (self.box[1][0] - self.box[0][0]) * at,
            self.box[0][1] + (self.box[1][1] - self.box[0][1]) * at,
            self.box[0][2] + (self.box[1][2] - self.box[0][2]) * at,
            self.box[0][3] + (self.box[1][3] - self.box[0][3]) * at,
        )
        res = PyWMWidgetDownstreamState(
            z_index=self.z_index[1] if at > 0.5 else self.z_index[0],
            box=box,
        )
        res.opacity = self.opacity[0] + at * (self.opacity[1] - self.opacity[0])
        res.lock_enabled=self.lock_enabled
        return res
