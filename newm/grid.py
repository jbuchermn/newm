#!/usr/bin/env python3
import math
import time

import logging

try:
    from .config import configured_value

    conf_time_scale = configured_value('grid.time_scale', .3)
    conf_throw_ps = configured_value('grid.throw_ps', [1, 5, 15])
    conf_min_dist = configured_value('grid.min_dist', .05)
except:
    pass

logger = logging.getLogger(__name__)

class Grid:
    def __init__(self, name, x0, x1, xi, d_ovr=0, m_snap=1):
        self.name = "%s-%d" % (name, time.time() % 1000)
        self.x0 = int(x0)
        self.x1 = int(x1)
        self.xi = int(xi)

        # Initially allow to handle xi out of bounds
        self.allow_out_of_bounds = True

        self.d_ovr = d_ovr
        self.m_snap = m_snap

        self.last_t = None

        self.last_x = None
        self.last_p = None

        self.last_x_output = None
        self.last_p_output = None

    def _get_bounds(self, x):
        if self.x0 <= x <= self.x1:
            self.allow_out_of_bounds = False

        x0, x1 = self.x0, self.x1
        if self.allow_out_of_bounds and x < x0:
            x0 = math.floor(x)
        if self.allow_out_of_bounds and x > x1:
            x1 = math.ceil(x)

        return x0, x1

    def at(self, x, silent=False):
        x0, x1 = self._get_bounds(x)

        t = time.time()
        if not silent:
            if self.last_x is not None and self.last_t is not None:
                dx = x - self.last_x
                dt = t - self.last_t
                self.last_p = dx / dt
            self.last_x = x

        xp = x
        if x < x0:
            if self.m_snap == 1:
                if self.d_ovr > 0:
                    y = x - x0
                    y = self.d_ovr*(1 / (1 - y/self.d_ovr) - 1)
                    xp = x0 + y
                else:
                    xp = x0
            else:
                y = max(0, x - x0 + 1)

                if y == 0:
                    xp = x0 - self.d_ovr
                else:
                    xp = x0 - self.d_ovr + self.d_ovr/(1. + ((1. - y)/y)**self.m_snap)

        elif x < x1:
            y = x - math.floor(x)

            if y == 0:
                xp = math.floor(x)
            else:
                xp = math.floor(x) + 1/(1. + ((1. - y)/y)**self.m_snap)

        else:
            if self.m_snap == 1:
                if self.d_ovr > 0:
                    y = x - x1
                    y = self.d_ovr*(1 / (1 + y/self.d_ovr) - 1)
                    xp = x1 - y
                else:
                    xp = x1
            else:
                y = min(1, max(0, x - x1))

                if y == 0:
                    xp = x1
                else:
                    xp = x1 + self.d_ovr/(1. + ((1. - y)/y)**self.m_snap)

        if not silent:
            if self.last_x_output is not None and self.last_t is not None:
                dx = xp - self.last_x_output
                dt = t - self.last_t
                self.last_p_output = dx / dt
            self.last_x_output = xp
            self.last_t = t

        # BEGIN DEBUG
        if not silent:
            logger.debug("GRID[%s]: %f, %f, %f, %f, %f",
                         self.name, time.time(), x, xp,
                         self.last_p if self.last_p is not None else 0,
                         self.last_p_output if self.last_p_output is not None else 0)
        # END DEBUG
        return xp

    def final(self, throw_dist_max=None):
        if throw_dist_max is None:
            throw_dist_max = 1. - conf_min_dist()

        if self.last_x_output is None:
            return self.at(self.xi), 0.

        x0, x1 = self._get_bounds(self.last_x_output)

        # Find final x
        x_base = self.last_x_output
        p = 0
        if self.last_p is not None:
            p = self.last_p

        x_finals = [round(x_base)]
        harder = False
        if p > 0:
            if x_finals[0] > x_base:
                harder = True

            x = x_finals[0] + 1
            while x < x_base + throw_dist_max:
                x_finals += [x]
                x += 1

        elif p < 0:
            if x_finals[0] < x_base:
                harder = True

            x = x_finals[0] - 1
            while x > x_base - throw_dist_max:
                x_finals = x_finals + [x]
                x -= 1

        ifinal = 0
        while ifinal < len(conf_throw_ps()):
            if abs(p) < conf_throw_ps()[ifinal]:
                break
            ifinal += 1
        if harder and ifinal > 0:
            ifinal -= 1
        xf = round(x_finals[min(ifinal, len(x_finals) - 1)])

        xf = min(x1, max(x0, round(xf)))
        dx = abs(self.last_x_output - xf)
        dt = dx * conf_time_scale()

        # Speed up animation if a high momentum is involved
        compare_t = abs(x_base - xf) / max(abs(p), 0.01)
        if compare_t < dt:
            dt = compare_t

        # BEGIN DEBUG
        x0 = self.at(self.last_x_output, silent=True)
        t0 = time.time()
        for i in range(2):
            logger.debug("GRID[%s]: %f, %f, %f, %f, %f",
                         self.name,
                         t0 + i * dt,
                         0,
                         x0 + i * (xf-x0),
                         0,
                         0 if dt == 0. else dx/dt if xf>x0 else -dx/dt)
        # END DEBUG

        return xf, dt


if __name__ == '__main__':
    import sys
    import matplotlib.pyplot as plt

    plots = {}
    with open(sys.argv[1], 'r') as inp:
        for l in inp:
            if "GRID[" in l:
                k = l.split("GRID[")[1]
                k, v = k.split("]:")
                if k not in plots:
                    plots[k] = []
                plots[k] += [v]

    print("----")
    for k in plots:
        print("* %s" % k)

    k = input("Plot? ")
    data = list(map(lambda arr: list(map(float, arr.split(","))), plots[k]))

    plt.figure()

    plt.plot([x[0] for x in data], [x[1] for x in data], 'bo-', label="Input translation")
    plt.plot([x[0] for x in data], [x[2] for x in data], 'go-', label="Output translation")
    plt.plot([x[0] for x in data], [x[3] for x in data], 'bo--', label="Input momentum")
    plt.plot([x[0] for x in data], [x[4] for x in data], 'go--', label="Output momentum")

    plt.legend()
    plt.show()
