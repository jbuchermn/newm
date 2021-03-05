from threading import Thread
import os
import time
import psutil
import logging

class SysBackend(Thread):
    def __init__(self, wm):
        super().__init__()
        self.wm = wm
        self._backlight = (
            "/sys/class/backlight/intel_backlight/brightness",
            "/sys/class/backlight/intel_backlight/max_brightness"
        )
        self._kbdlight = (
            "/sys/class/leds/smc::kbd_backlight/brightness",
            "/sys/class/leds/smc::kbd_backlight/max_brightness"
        )

        self._running = True
        self.start()

    def run(self):
        while self._running:
            time.sleep(1.)
            bat = psutil.sensors_battery()
            if bat.percent < 15 and not bat.power_plugged:
                self.wm.panel_endpoint.broadcast({
                    'kind': 'sys_backend',
                    'battery': bat.percent / 100.
                })

    def stop(self):
        self._running = False

    def set_backlight(self, delta_perc):
        try:
            cur = int(open(self._backlight[0], 'r').read()[:-1])
            cur_max = int(open(self._backlight[1], 'r').read()[:-1])

            cur += int(cur_max * delta_perc / 100.0)
            cur = max(min(cur_max, cur), 0)

            open(self._backlight[0], 'w').write("%d" % cur)

            self.wm.panel_endpoint.broadcast({
                'kind': 'sys_backend',
                'backlight': 1. * cur / cur_max
            })

            return True
        except Exception:
            logging.exception("Error setting backlight")
            return False

    def set_kbdlight(self, delta_perc):
        try:
            cur = int(open(self._kbdlight[0], 'r').read()[:-1])
            cur_max = int(open(self._kbdlight[1], 'r').read()[:-1])

            cur += int(cur_max * delta_perc / 100.0)
            cur = max(min(cur_max, cur), 0)

            open(self._kbdlight[0], 'w').write("%d" % cur)

            self.wm.panel_endpoint.broadcast({
                'kind': 'sys_backend',
                'kbdlight': 1. * cur / cur_max
            })

            return True

        except Exception:
            logging.exception("Error setting kbdlight")
            return False

    def set_vol(self, delta_perc, mute=False):
        if mute:
            os.system("amixer sset Master 0%")

            self.wm.panel_endpoint.broadcast({
                'kind': 'sys_backend',
                'volume': 0
            })
        else:
            os.system("amixer sset Master %d%%%s" % (abs(delta_perc), "+" if delta_perc > 0 else "-"))

            try:
                res = int(os.popen("amixer sget Master | grep 'Mono:'").read().split('[')[1].split('%]')[0])
                
                self.wm.panel_endpoint.broadcast({
                    'kind': 'sys_backend',
                    'volume': res / 100.
                })
            except Exception as e:
                logging.exception("Error getting volume")

        return True

    def register_xf86_keybindings(self):
        self.wm.key_processor.register_bindings(
            ("XF86MonBrightnessUp", lambda: self.set_backlight(+10)),
            ("XF86MonBrightnessDown", lambda: self.set_backlight(-10)),
            ("XF86LaunchA", lambda: logging.info("LaunchA")),
            ("XF86LaunchB", lambda: logging.info("LaunchB")),
            ("XF86KbdBrightnessUp",  lambda: self.set_kbdlight(+10)),
            ("XF86KbdBrightnessDown", lambda: self.set_kbdlight(-10)),
            ("XF86AudioPrev", lambda: logging.info("AudioPrev")),
            ("XF86AudioPlay", lambda: logging.info("AudioPlay")),
            ("XF86AudioNext", lambda: logging.info("AudioNext")),
            ("XF86AudioMute", lambda: self.set_vol(0, mute=True)),
            ("XF86AudioLowerVolume", lambda: self.set_vol(-10)),
            ("XF86AudioRaiseVolume", lambda: self.set_vol(+10))
        )


