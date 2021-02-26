#!/usr/bin/env python3
import math
import time

# TODO
import logging

TIME_SCALE = .3

class Grid:
    def __init__(self, x0, x1, xi, d_ovr=0, m_snap=1):
        self.x0 = int(x0)
        self.x1 = int(x1)
        self.xi = int(xi)

        self.d_ovr = d_ovr
        self.m_snap = m_snap

        self.last_x = None
        self.last_t = None
        self.last_p = None

    def at(self, x):
        t = time.time()
        if self.last_x is not None and self.last_t is not None:
            dx = x - self.last_x
            dt = t - self.last_t
            self.last_p = dx / dt
        self.last_x = x
        self.last_t = t

        if x < self.x0:
            if self.m_snap == 1:
                if self.d_ovr > 0:
                    y = x - self.x0
                    y = self.d_ovr*(1 / (1 - y/self.d_ovr) - 1)
                    return self.x0 + y
                else:
                    return self.x0
            else:
                y = max(0, x - self.x0 + 1)

                if y == 0:
                    return self.x0 - self.d_ovr
                else:
                    return self.x0 - self.d_ovr + self.d_ovr/(1. + ((1. - y)/y)**self.m_snap)

        elif x < self.x1:
            y = x - math.floor(x)

            if y == 0:
                return math.floor(x)
            else:
                return math.floor(x) + 1/(1. + ((1. - y)/y)**self.m_snap)

        else:
            if self.m_snap == 1:
                if self.d_ovr > 0:
                    y = x - self.x1
                    y = self.d_ovr*(1 / (1 + y/self.d_ovr) - 1)
                    return self.x1 - y
                else:
                    return self.x1
            else:
                y = min(1, max(0, x - self.x1))

                if y == 0:
                    return self.x1
                else:
                    return self.x1 + self.d_ovr/(1. + ((1. - y)/y)**self.m_snap)

    def final(self, restrict_by_xi=0, restrict_by_x_current=False):
        if self.last_x is None:
            return self.x0, 0.

        if self.last_p is None or self.last_t is None or (time.time() - self.last_t > TIME_SCALE):
            xf = self.last_x
            self.last_p = 0
        else:
            xf = self.last_x + self.last_p * TIME_SCALE

        xf = round(xf)

        if restrict_by_x_current:
            xf = min(math.ceil(self.last_x), max(math.floor(self.last_x), xf))
        elif restrict_by_xi > 0:
            xf = min(self.xi + restrict_by_xi, max(self.xi - restrict_by_xi, xf))

        xf = min(self.x1, max(self.x0, round(xf)))
        dx = abs(self.last_x - xf)

        dt = dx / abs(self.last_p) if self.last_p is not None and abs(self.last_p) > 0 else TIME_SCALE
        if dt > TIME_SCALE:
            dt = TIME_SCALE

        return xf, dt


if __name__ == '__main__':
    import numpy as np
    import matplotlib.pyplot as plt

    grid = Grid(0, 2, 1, .2, 2)

    xs = np.linspace(-2, 4, 100)
    ys = np.zeros_like(xs)
    for i, x in enumerate(xs):
        ys[i] = grid.at(x)

    plt.figure()
    plt.plot(xs, ys)
    plt.show()
