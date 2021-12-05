# newm
[![License](https://img.shields.io/github/license/jbuchermn/newm)](LICENSE)
[![AUR](https://img.shields.io/aur/version/newm-git)](https://aur.archlinux.org/packages/newm-git)

[![IMAGE](https://github.com/jbuchermn/newm/blob/master/newm/resources/screenshot.png)](https://youtu.be/otMEC03ie0g)

## Idea

**newm** is a Wayland compositor written with laptops and touchpads in mind. The idea is, instead of placing windows inside the small viewport (that is, the monitor) to arrange them along an arbitrarily large two-dimensional wall (generally without windows overlapping) and focus the compositors job on moving around along this wall efficiently and providing ways to the user to rearrange the wall such that he finds the overall layout intuitive.

So, windows are placed on a two-dimensional grid of tiles taking either one by one, one by two, two by one, ... tiles of that grid. The compositor shows a one by one, two by two, ... view of that grid but scales the windows so they are usable on any zoom level (that is, zooming out the compositor actually changes the windows sizes). This makes for example switching between a couple of fullscreen applications very easy - place them in adjacent one by one tiles and have the compositor show a one by one view. And if you need to see them in parallel, zoom out. Then back in, and so on...

The basic commands therefore are navigation (left, right, top, bottom) and zoom-in and -out. These commands can be handled very intuitively on the touchpad (one- and two-finger gestures are reserved for interacting with the apps):
- Use three fingers to move around the wall
- Use four fingers to zoom out (move them upward) or in (downward)

To be able to arange the windows in a useful manner, use
- `Logo` (unless configured otherwise) plus one finger on the touchpad to move windows
- `Logo` (unless configured otherwise) plus two fingers on the touchpad to change the extent of a window

To get a quick overview of all windows, just hit the Logo (unless configured otherwise) key.
Additionally with a quick 5-finger swipe a launcher panel can be opened.

These behaviours can (partly) be configured (see below for setup). By default (check [default_config.py](newm/default_config.py)), the following key bindings (among others) are in place
- `Logo-hjkl`: Move around
- `Logo-un`: Scale
- `Logo-HJKL`: Move windows around
- `Logo-Ctrl-hjkl`: Resize windows
- `Logo-f`: Toggle a fullscreen view of the focused window (possibly resizing it)
- ...

## newm v0.2

TODO v0.2 is almost ready to be merged into master.

Changes include
- Support for multi-monitor setups
- Basic support for layer shell (waybar, rofi, ...)
- Many small improvements concerning window behaviour
- Virtual output support (see [newm-sidecar](https://github.com/jbuchermn/newm-sidecar))
- More configuration possibilities, as e.g. defining which windows should float
- Improved background
- Possibility to switch windows between tiled and floating


## Installing

### Arch Linux

For Arch Linux users, an AUR package `newm-git` is provided. Alternatively, see below for pip installation.

### Installing with pip

[pywm](https://github.com/jbuchermn/pywm) is the abstraction layer for and main dependency of newm. If all prerequisites are installed, the command:

``` sh
pip3 install --user git+https://github.com/jbuchermn/pywm
```

should suffice.Additionally, unless configured otherwise, newm depends on alacritty for a default terminal emulator.

To install newm:

``` sh
pip3 install --user git+https://github.com/jbuchermn/newm
```

Installing newm this way means it cannot be used as a login manager, as it can only be started by your current user (see below)

### Starting and tests

Start newm using

``` sh
start-newm -d
```

`-d` is the debug flag and gives more output to `$HOME/.cache/newm_log`.

Open a terminal window (default `alacritty`) using `Logo+Enter` (default config). Check if the touchpad works by pressing `Logo` and resizing the window using two-finger touch. If the touchpad does not work (and you intend to use it), check that your user has access by either command:

```
ls -al /dev/input/event*
evtest
```

More details about this can be found on the troubleshooting page of [pywm](https://github.com/jbuchermn/pywm).

## Configuration

### Setting up the config file and first example

Configuring is handled via Python and read from either `$HOME/.config/newm/config.py` or (lower precedence) `/etc/newm/config.py`. Take `default_config.py` as a basis; details on the possible keys are provided below.

For example, copy (path of `default_config.py` in the example assumes pip installation)

``` sh
cd
mkdir -p .config/newm
cp .local/lib/pythonX.Y/site-packages/newm/default_config.py .config/newm/config.py
vim .config/newm/config.py
```

and adjust, e.g. for a German HiDPI MacBook with a wallpaper placed in the home folder,

``` py
import os
from pywm import (
    PYWM_MOD_LOGO,
    PYWM_MOD_ALT
)

mod = PYWM_MOD_ALT

def on_startup():
    os.system("waybar &")

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

The configuration works by evaluating the python config file and extracting the variables which the file exports. So basically you can do whatever you please to provide the configuration values, this is why certain config elements are callbacks. Some elements are hierarchical, to set these use PYthon dicts - e.g. for `x.y`:

```py
x = {
    'y': 2.0
}
```


The configuration can be dynamically updated (apart from a couple of fixed keys) using `Layout.update_config` (by default bound to `Mod+C`).

See [config](./doc/config.md) for a documentation on all configurable values.

## Next steps

### Tips and tricks, setting up environment and systemd integration

[Link](./doc/tips_and_tricks.md)
[Link](./doc/env_wayland.md)
[Link](./doc/systemd.md)

### Using newm-cmd

`newm-cmd` provides a way to interact with a running newm instance from command line:
- `newm-cmd inhibit-idle` prevents newm from going into idle states (dimming the screen)
- `newm-cmd config` reloads the configuration
- `newm-cmd lock` locks the screen
- `newm-cmd open-virtual-output <name>` opens a new virtual output (see [newm-sidecar](https://github.com/jbcuhermn/newm-sidecar))
- `newm-cmd close-virtual-output <name>` close a virtual output
- `newm-cmd clean` removes orphaned states, which can happen, but shouldn't (if you encounter the need for this, please file a bug)
- `newm-cmd debug` prints out some debug info on the current state of views

### Using newm for login

This setup depends on [greetd](https://git.sr.ht/~kennylevinsen/greetd). Make sure to install newm as well as pywm and a newm panel in a way in which the greeter-user has access, i.e. either form the AUR, or e.g.:

``` sh
sudo pip3 install git+https://github.com/jbuchermn/pywm
sudo pip3 install git+https://github.com/jbuchermn/newm
```

Place configuration in `/etc/newm/config.py` and check, after logging in as `greeter`, that `start-newm` works and shows the login panel (login itself should not work). If it works, set

``` toml
command = "start-newm"
```

in `/etc/greetd/config.toml`.

