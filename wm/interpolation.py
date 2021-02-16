from pywm import PyWMViewDownstreamState, PyWMWidgetDownstreamState

class ViewDownstreamInterpolation:
    def __init__(self, state0, state1):
        self.z_index = (state0.z_index, state1.z_index)
        self.box = (state0.box, state1.box)
        self.corner_radius = (state0.corner_radius, state1.corner_radius)
        self.accepts_input = state1.accepts_input
        self.size = (state0.size, state1.size)

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

        res.size=self.size[1] if at > 0.5 else self.size[0]
        # res.size=self.size[1] if sum(self.size[1]) > sum(self.size[0]) else self.size[0]
        return res

class WidgetDownstreamInterpolation:
    def __init__(self, state0, state1):
        self.z_index = (state0.z_index, state1.z_index)
        self.box = (state0.box, state1.box)

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
        return res
