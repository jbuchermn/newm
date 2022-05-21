# newm

[![License](https://img.shields.io/github/license/jbuchermn/newm)](LICENSE)
[![AUR](https://img.shields.io/aur/version/newm-git)](https://aur.archlinux.org/packages/newm-git)
[![Join the chat at https://gitter.im/jbuchermn-newm/community](https://badges.gitter.im/jbuchermn-newm/community.svg)](https://gitter.im/jbuchermn-newm/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![IMAGE](https://github.com/jbuchermn/newm/blob/master/newm/resources/screenshot.png)](https://youtu.be/Qvyt4XynlYI)

## Idea

**newm** is a Wayland compositor written with laptops and touchpads in mind. The idea is, instead of placing windows inside the small viewport (that is, the monitor) to arrange them along an arbitrarily large two-dimensional wall (generally without windows overlapping) and focus the compositors job on moving around along this wall efficiently and providing ways to the user to rearrange the wall such that he finds the overall layout intuitive.

So, windows are placed on a two-dimensional grid of tiles taking either one by one, one by two, two by one, ... tiles of that grid. The compositor shows a one by one, two by two, ... view of that grid but scales the windows so they are usable on any zoom level (that is, zooming out the compositor actually changes the windows sizes). This makes for example switching between a couple of fullscreen applications very easy - place them in adjacent one by one tiles and have the compositor show a one by one view. And if you need to see them in parallel, zoom out. Then back in, and so on...

The basic commands therefore are navigation (left, right, top, bottom) and zoom-in and -out. These commands can be handled very intuitively on the touchpad (one- and two-finger gestures are reserved for interacting with the apps):

- Use three fingers to move around the wall
- Use four fingers to zoom out (move them upward) or in (downward)

To be able to arrange the windows in a useful manner, use

- `Logo` (default , unless configured otherwise) + one finger on the touchpad to move windows
- `Logo` (default , unless configured otherwise) + two fingers on the touchpad to change the extent of a window

To get a quick overview of all windows, just hit the `Logo` (default , unless configured otherwise) key.
Additionally with a quick 5-finger swipe a launcher panel can be opened.

These behaviours can (partly) be configured (see below for setup). By default (check [default_config.py](newm/default_config.py)), the following key bindings (among others) are in place

- `Logo-hjkl`: Move around
- `Logo-un`: Scale
- `Logo-HJKL`: Move windows around
- `Logo-Ctrl-hjkl`: Resize windows
- `Logo-f`: Toggle a fullscreen view of the focused window (possibly resizing it)
- ...

## Roadmap

v0.3 has been merged into master, new features include

- [x] Improve panel functionality
- [X] Better bars
  - [X] Support always-present top and bottom bars
  - [ ] Slide in bars
- [x] Borders
  - [x] Draw borders around some floating windows (quite ugly floating windows on v0.2)
  - [x] Possibly highlight focused window using a border
- [x] Enable window swallowing
- [X] Blurred window backgrounds
- [X] Better key bindings
- [X] DBus gestures
- [ ] Better window stacking


## Installing

### Arch Linux

- [Intall on Arch linux](doc/install_Arch_Linux.md)

### NixOS

Install via flakes (see also [dotfiles-nix](https://github.com/jbuchermn/dotfiles-nix)):

```sh
nix build "github:jbuchermn/newm#newm"
./result/bin/start-newm -d
```

Note that this probably does not work outside nixOS. To fix OpenGL issues on other
linux distros using nix as a (secondary) package manager, see
[nixGL](https://github.com/guibou/nixGL). Additionally, PAM authentication appears
to be broken in this setup.

### Installing with pip

[pywm](https://github.com/jbuchermn/pywm) is the abstraction layer for and main dependency of newm. If all prerequisites are installed, the command:

```sh
pip3 install --user git+https://github.com/jbuchermn/pywm
```

should suffice.Additionally, unless configured otherwise, newm depends on alacritty for a default terminal emulator.

To install newm:

```sh
pip3 install --user git+https://github.com/jbuchermn/newm
```

Installing newm this way means it cannot be used as a login manager, as it can only be started by your current user (see below)

### Starting and tests

Start newm using

```sh
start-newm -d
```

`-d` is the debug flag and gives more output to `$HOME/.cache/newm_log`.


## Configuration

### Setting up the config file and first example

Configuring is handled via Python and read from either `$HOME/.config/newm/config.py` or (lower precedence) `/etc/newm/config.py`. Take `default_config.py` as a basis; details on the possible keys are provided below.

For example, copy (path of `default_config.py` in the example assumes pip installation)

```sh
cd
mkdir -p .config/newm
cp .local/lib/pythonX.Y/site-packages/newm/default_config.py .config/newm/config.py
vim .config/newm/config.py
```

and adjust, e.g. for a German HiDPI MacBook with a wallpaper placed in the home folder,

```py
import os
from pywm import (
    PYWM_MOD_LOGO,
    PYWM_MOD_ALT
)

def on_startup():
    os.system("waybar &")

def on_reconfigure():
    os.system("notify-send newm \"Reloaded configuration\" &")

bar = {
    'enabled': False,
}

background = {
    'path': os.environ['HOME'] + '/wallpaper.jpg'
}

outputs = [
    { 'name': 'eDP-1', 'scale': 2. }
]

pywm = {
    'xkb_model': "macintosh",
    'xkb_layout': "de,de",
    'xkb_options': "caps:escape",
}
```

### Configuring

The configuration works by evaluating the python config file and extracting the variables which the file exports. So basically you can do whatever you please to provide the configuration values, this is why certain config elements are callbacks. Some elements are hierarchical, to set these use Python dicts - e.g. for `x.y`:

```py
x = {
    'y': 2.0
}
```

The configuration can be dynamically updated (apart from a couple of fixed keys) using `Layout.update_config` (by default bound to `Mod+C`).

See [config](./doc/config.md) for a documentation on all configurable values.

Be aware that functions (as in keybindings, `on_startup`, ...) are run synchronously in the compositor thread. Blocking there will block the whole system.

### Troubleshooting: Touchpad

It is very much encouraged to use evdev, instead of python gestures (see [config](./doc/config.md)), however these might not work right from the start. Try:

```
ls -al /dev/input/event*
evtest
```

This is a required prerequisite to use the python-side (smoother) gestures. C-side or DBus gestures do not require this.

As a sidenote, this is not necessary for a Wayland compositor in general as the devices can be accessed through `systemd-logind` or `seatd` or similar.
However the python `evdev` module does not allow instantiation given a file descriptor (only a path which it then opens itself),
so usage of that module would no longer be possible in this case (plus at first sight there is no easy way of getting that file descriptor to the 
Python side). Also `wlroots` (`libinput` in the backend) does not expose touchpads as what they are (`touch-down`, `touch-up`, `touch-motion` for any
number of parallel slots), but only as pointers (`motion` / `axis`), so gesture detection around `libinput`-events is not possible as well.

Therefore, we're stuck with the less secure (and a lot easier) way of using the (probably named `input`) group.

## Next steps

- [Tips and tricks](./doc/tips_and_tricks.md)
- [Environment setup](./doc/env_wayland.md)
- [Systemd integration](./doc/systemd.md)
- [Look and feel](./doc/look_and_feel.md)

### Using newm-cmd

`newm-cmd` provides a way to interact with a running newm instance from command line:

- `newm-cmd inhibit-idle` prevents newm from going into idle states (dimming the screen)
- `newm-cmd config` reloads the configuration
- `newm-cmd lock` locks the screen
- `newm-cmd open-virtual-output <name>` opens a new virtual output (see [newm-sidecar](https://github.com/jbuchermn/newm-sidecar))
- `newm-cmd close-virtual-output <name>` close a virtual output
- `newm-cmd clean` removes orphaned states, which can happen, but shouldn't (if you encounter the need for this, please file a bug)
- `newm-cmd debug` prints out some debug info on the current state of views
- `newm-cmd unlock` unlocks the compositor (if explicitly enabled in config) - this is useful in case you have trouble setting up the lock screen.

### Using newm for login

This setup depends on [greetd](https://git.sr.ht/~kennylevinsen/greetd). Make sure to install newm as well as pywm and a newm panel in a way in which the greeter-user has access, i.e. either form the AUR, or e.g.:

```sh
sudo pip3 install git+https://github.com/jbuchermn/pywm
sudo pip3 install git+https://github.com/jbuchermn/newm
```

Place configuration in `/etc/newm/config.py` and check, after logging in as `greeter`, that `start-newm` works and shows the login panel (login itself should not work). If it works, set

```toml
command = "start-newm"
```

in `/etc/greetd/config.toml`.
