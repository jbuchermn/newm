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

    def on_key(self, pressed, keysyms, mod_down, ctrl_down):
        triggered = False
        for b in self.bindings:
            if b.process(pressed, keysyms, mod_down, ctrl_down):
                triggered = True

        return triggered

