import os

"""
TODO: Outsource this + make it configurable or autodetecting...
"""
def set_light(backlight, up):
    try:
        p = ""
        p_max = ""
        if backlight:
            p = "/sys/class/backlight/intel_backlight/brightness"
            p_max = "/sys/class/backlight/intel_backlight/max_brightness"
        else:
            p = "/sys/class/leds/smc::kbd_backlight/brightness"
            p_max = "/sys/class/leds/smc::kbd_backlight/max_brightness"

        cur = int(open(p, 'r').read()[:-1])
        cur_max = int(open(p_max, 'r').read()[:-1])
        if up:
            cur += cur_max / 12.
        else:
            cur = max(0, cur - cur_max / 12.)
        open(p, 'w').write("%d" % cur)
    except Exception:
        pass

def set_vol(cmd):
    if cmd == 0:
        os.system("amixer sset Master 0%")
    elif cmd == 10:
        os.system("amixer sset Master 10%+")
    elif cmd == -10:
        os.system("amixer sset Master 10%-")



class KeyBinding:
    def __init__(self, keys, action):
        self.mod = False
        self.ctrl = False
        keys = keys.split("-")
        for k in keys[:-1]:
            if k == "M":
                self.mod = True
            if k == "C":
                self.ctrl = True

        self.keysym = keys[-1]
        self.action = action

        self._ready_to_fire = False

    def process(self, pressed, keysyms, mod_down, ctrl_down):
        if pressed and keysyms == self.keysym and \
                mod_down == self.mod and \
                ctrl_down == self.ctrl:
            self._ready_to_fire = True
            return True

        if not pressed and keysyms == self.keysym and \
                self._ready_to_fire:
            self._ready_to_fire = False
            self.action()
            return True

        return False


class ModPressKeyBinding:
    def __init__(self, mod_sym, action):
        self.mod_sym = mod_sym
        self.action = action
        self._ready_to_fire = False

    def process(self, pressed, keysyms, mod_down, ctrl_down):
        if self.mod_sym not in keysyms:
            self._ready_to_fire = False
            return False

        if pressed:
            self._ready_to_fire = True
        elif self._ready_to_fire:
            self.action()

        return True


def keybinding_factory(processor, keys, action):
    if keys == "ModPress":
        return ModPressKeyBinding(processor.mod_sym, action)
    else:
        return KeyBinding(keys, action)


class KeyProcessor:
    def __init__(self, mod_sym):
        self.mod_sym = mod_sym
        self.bindings = []

    def register_bindings(self, *bindings):
        for keys, action in bindings:
            self.bindings += [keybinding_factory(self, keys, action)]

    def register_xf86_bindings(self):
        self.register_bindings(
            ("XF86MonBrightnessUp", lambda: set_light(True, True)),
            ("XF86MonBrightnessDown", lambda: set_light(True, False)),
            ("XF86LaunchA", lambda: print("LaunchA")),
            ("XF86LaunchB", lambda: print("LaunchB")),
            ("XF86KbdBrightnessUp",  lambda: set_light(False, True)),
            ("XF86KbdBrightnessDown", lambda: set_light(False, False)),
            ("XF86AudioPrev", lambda: print("AudioPrev")),
            ("XF86AudioPlay", lambda: print("AudioPlay")),
            ("XF86AudioNext", lambda: print("AudioNext")),
            ("XF86AudioMute", lambda: set_vol(0)),
            ("XF86AudioLowerVolume", lambda: set_vol(-10)),
            ("XF86AudioRaiseVolume", lambda: set_vol(10))
        )


    def on_key(self, pressed, keysyms, mod_down, ctrl_down):
        triggered = False
        for b in self.bindings:
            if b.process(pressed, keysyms, mod_down, ctrl_down):
                triggered = True

        return triggered

