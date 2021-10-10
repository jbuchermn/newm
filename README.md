# newm
[![IMAGE](https://github.com/jbuchermn/newm/blob/master/newm/resources/screenshot.png)](https://youtu.be/otMEC03ie0g)
(Wayland compositor)

## Idea

**newm** is a Wayland compositor written with laptops and touchpads in mind. The idea is, instead of placing windows inside the small viewport (that is, the monitor) to arrange them along an arbitrarily large two-dimensional wall (generally without windows overlapping) and focus the compositors job on moving around along this wall efficiently and providing ways to the user to rearrange the wall such that he finds the overall layout intuitive.

So, windows are placed on a two-dimensional grid of tiles taking either one by one, one by two, two by one, ... tiles of that grid. The compositor shows a one by one, two by two, ... view of that grid but scales the windows so they are usable on any zoom level (that is, zooming out the compositor actually changes the windows sizes). This makes switching between a couple of fullscreen applications very easy - place them in adjacent one by one tiles and have the compositor show a one by one view. And so on...

The basic commands therefore are navigation (left, right, top, bottom) and zoom-in and -out. These commands can be handled very intuitively on the touchpad (one- and two-finger gestures are reserved for interacting with the apps):
- Use three fingers to move around the wall
- Use four fingers to zoom out (move them upward) or in (downward)

To be able to arange the windows in a useful manner, use
- Logo (unless configured otherwise) plus one finger on the touchpad to move windows
- Logo (unless configured otherwise) plus two fingers on the touchpad to change the extent of a window

To get a quick overview of all windows, just hit the Mod (that is, unless configured otherwise, the Logo) key.

These behaviours can (partly) be configured (see below for setup). By default (check [default_config.py](newm/default_config.py)), for example the following key bindings are in place
- `Logo-hjkl`: Move around
- `Logo-HJKL`: Move windows around
- `Logo-Ctrl-hjkl`: Resize windows
- `Logo-f`: Toggle a fullscreen view of the focused window (possibly resizing it)
- ...

## Status and limitations

This is the first release of newm. Therefore a lot of configurable behaviour, quality of documentation and the like is still missing. However the basic building blocks have been in use on my machine from the beginning (2018) continuously.

The most relevant functional limitation at the moment is missing support for multi-monitor setups. Apart from that see [pywm](https://github.com/jbuchermn/pywm) for known issues concerning certain applications.

## Installing

### Arch Linux

For Arch Linux users, an AUR package `newm-git` is provided. Alternatively, see below for pip installation.

### Prerequisites and pywm

[pywm](https://github.com/jbuchermn/pywm) is the abstraction layer for and main dependency of newm. If all prerequisites are installed, the command:

``` sh
pip3 install git+https://github.com/jbuchermn/pywm
```

should suffice.

Additionally, unless configured otherwise, newm depends on alacritty for a default terminal emulator.

### Single-user installation (without newm-login, preferred)

To install newm:

``` sh
pip3 install git+https://github.com/jbuchermn/newm
```

Start it using

``` sh
start-newm
```

See also [pywm](https://github.com/jbuchermn/pywm) for troubleshooting.

### Configuring

#### Setting up the config file

Configuring is handled via Python and read from either `$HOME/.config/newm/config.py` or (lower precedence) `/etc/newm/config.py`. Take `default_config.py` as a basis and check the source code for usages of `configured_value` to get more details about the different keys.

For example, copy (path of `default_config.py` in the example assumes pip installation)

``` sh
cd
mkdir -p .config/newm
cp .local/lib/pythonX.Y/site-packages/newm/default_config.py .config/newm/config.py
vim .config/newm/config.py
```

and adjust:

``` py
import os
from pywm import (
    PYWM_MOD_LOGO,
    PYWM_MOD_ALT
)

mod = PYWM_MOD_ALT
wallpaper = os.environ['HOME'] + '/wallpaper.jpg'
```


#### Lock on hibernate

This can be achieved for example by placing the following in `/lib/systemd/system-sleep/00-lock.sh`

``` sh
#!/bin/sh
newm-cmd lock-$1 
```

### Multi-user installation (to use newm for login)

This setup depends on [greetd](https://git.sr.ht/~kennylevinsen/greetd). Make sure to install newm as well as pywm in a way in which the greeter-user has access, e.g.:

``` sh
sudo pip3 install git+https://github.com/jbuchermn/pywm
sudo pip3 install git+https://github.com/jbuchermn/newm
```

Place configuration in `/etc/newm/config.py` and check, after logging in as `greeter`, that `start-newm` works and shows the login panel (login itself should not work). If it works, set

``` toml
command = "start-newm"
```

in `/etc/greetd/config.toml`.

## Panel

See [newm-panel-nwjs](https://github.com/jbuchermn/newm-panel-nwjs) for a different panel implementation (launcher, locker, notifiers) based on NW.js.
