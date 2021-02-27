#!/usr/bin/env python3
import math
import time

import logging

TIME_SCALE = .3

class Grid:
    def __init__(self, name, x0, x1, xi, d_ovr=0, m_snap=1):
        self.name = "%s-%d" % (name, time.time() % 1000)
        self.x0 = int(x0)
        self.x1 = int(x1)
        self.xi = int(xi)

        self.d_ovr = d_ovr
        self.m_snap = m_snap

        self.last_x = None
        self.last_t = None
        self.last_p = None

    def at(self, x, silent=False):
        if not silent:
            t = time.time()
            if self.last_x is not None and self.last_t is not None:
                dx = x - self.last_x
                dt = t - self.last_t
                self.last_p = dx / dt
            self.last_x = x
            self.last_t = t

        xp = x
        if x < self.x0:
            if self.m_snap == 1:
                if self.d_ovr > 0:
                    y = x - self.x0
                    y = self.d_ovr*(1 / (1 - y/self.d_ovr) - 1)
                    xp = self.x0 + y
                else:
                    xp = self.x0
            else:
                y = max(0, x - self.x0 + 1)

                if y == 0:
                    xp = self.x0 - self.d_ovr
                else:
                    xp = self.x0 - self.d_ovr + self.d_ovr/(1. + ((1. - y)/y)**self.m_snap)

        elif x < self.x1:
            y = x - math.floor(x)

            if y == 0:
                xp = math.floor(x)
            else:
                xp = math.floor(x) + 1/(1. + ((1. - y)/y)**self.m_snap)

        else:
            if self.m_snap == 1:
                if self.d_ovr > 0:
                    y = x - self.x1
                    y = self.d_ovr*(1 / (1 + y/self.d_ovr) - 1)
                    xp = self.x1 - y
                else:
                    xp = self.x1
            else:
                y = min(1, max(0, x - self.x1))

                if y == 0:
                    xp = self.x1
                else:
                    xp = self.x1 + self.d_ovr/(1. + ((1. - y)/y)**self.m_snap)

        # BEGIN DEBUG
        if not silent:
            logging.debug("GRID[%s]: %f, %f, %f, %f",
                          self.name, time.time(), x, xp, self.last_p)
        # END DEBUG
        return xp

    def final(self, restrict_by_xi=0, restrict_by_x_current=False):
        if self.last_x is None:
            return self.at(self.xi), 0.

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

        # BEGIN DEBUG
        x0 = self.at(self.last_x, silent=True)
        t0 = time.time()
        for i in range(100):
            logging.debug("GRID[%s]: %f, %f, %f, %f",
                          self.name,
                          t0 + i/100. * dt,
                          0,
                          x0 + i/100. * (xf-x0),
                          dx/dt if xf>x0 else -dx/dt)
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

    plt.plot([x[0] for x in data], [x[1] for x in data], label="Input translation")
    plt.plot([x[0] for x in data], [x[2] for x in data], label="Output translation")
    plt.plot([x[0] for x in data], [x[3] for x in data], label="Input momentum")

    plt.legend()
    plt.show()
