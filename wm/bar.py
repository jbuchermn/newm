from abc import abstractmethod
from threading import Thread
import os
import pwd
import time
import cairo
import psutil
from pywm import PyWMCairoWidget

BAR_HEIGHT = 20


class Bar(PyWMCairoWidget):
    def __init__(self, wm):
        super().__init__(wm, int(wm.config['output_scale'] * wm.width), int(wm.config['output_scale'] * BAR_HEIGHT))
        self.set_z_index(5)

        self.texts = ["Leftp", "Middlep", "Rightp"]
        self.font_size = wm.config['output_scale'] * 12

        self.update()

    @abstractmethod
    def update(self):
        pass

    def set_texts(self, texts):
        self.texts = texts
        self.render()

    def _render(self, surface):
        ctx = cairo.Context(surface)

        ctx.set_source_rgba(.0, .0, .0, .7)
        ctx.rectangle(0, 0, self.width, self.height)
        ctx.fill()

        ctx.select_font_face('Source Code Pro for Powerline')
        ctx.set_font_size(self.font_size)

        _, y_bearing, c_width, c_height, _, _ = ctx.text_extents("pA")
        c_width /= 2

        total_text_width = sum([len(t) for t in self.texts])
        spacing = self.width - total_text_width * c_width
        spacing /= len(self.texts)

        x = spacing/2.
        for t in self.texts:
            ctx.move_to(x, self.height/2 - c_height/2 - y_bearing)
            ctx.set_source_rgb(1., 1., 1.)
            ctx.show_text(t)
            x += len(t) * c_width + spacing

        ctx.stroke()


class TopBar(Bar, Thread):
    def __init__(self, wm):
        Bar.__init__(self, wm)
        Thread.__init__(self)

        self._running = True
        self.start()

    def stop(self):
        self._running = False

    def update(self):
        dy = self.wm.state.top_bar_dy * BAR_HEIGHT
        self.set_box(0, dy - BAR_HEIGHT, self.wm.width, BAR_HEIGHT)

    def run(self):
        while self._running:
            self.set()
            time.sleep(1.)

    def set(self):
        bat = psutil.sensors_battery()
        uname = pwd.getpwuid(os.getuid())[0]
        self.set_texts(
            [uname,
             time.strftime("%c"),
             "%d%% %s" % (bat.percent, "↑" if bat.power_plugged else "↓")])

class BottomBar(Bar, Thread):
    def __init__(self, wm):
        Bar.__init__(self, wm)
        Thread.__init__(self)

        self._running = True
        self.start()

    def stop(self):
        self._running = False

    def update(self):
        dy = self.wm.state.bottom_bar_dy * BAR_HEIGHT
        self.set_box(0, self.wm.height - dy, self.wm.width,
                     BAR_HEIGHT)

    def run(self):
        while self._running:
            self.set()
            time.sleep(1.)

    def set(self):
        cpu_perc = psutil.cpu_percent(interval=1)
        ifdevice = "wlan0"
        ip = ""
        try:
            ip = psutil.net_if_addrs()[ifdevice][0].address
        except Exception:
            ip = "-/-"
        mem_perc = psutil.virtual_memory().percent
        self.set_texts(
            ["CPU: %d%%" % cpu_perc,
             "%s: %s" % (ifdevice, ip),
             "RAM: %d%%" % mem_perc])

