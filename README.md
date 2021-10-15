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

### Starting and tests

Start newm using

``` sh
start-newm
```

Open a terminal window (default `alacritty`) using `Logo+Enter` (default config). Check if the touchpad works by pressing `Logo` and resizing the window using two-finger touch. If the touchpad does not work (and you intend to use it), check that your user has access by either command:

```
ls -al /dev/input/event*
evtest
```

More details about this can be found on the troubleshooting page of [pywm](https://github.com/jbuchermn/pywm).

### Configuration

#### Setting up the config file and first example

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
wallpaper = os.environ['HOME'] + '/wallpaper.jpg'

output_scale = 2.0
round_scale = 2.0

pywm = {
    'xkb_model': "macintosh",
    'xkb_layout': "de,de",
    'xkb_options': "caps:escape",
}
```

#### Configuring

Work in progress
- Config file format
    - Dots are hierarchies (python dicts)
- Reload
- Fill out / Structure



| Configuration key                       | Default value                          | Description                                                                                                                                                                                          |
|-----------------------------------------|----------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `output_scale`                          | `1.0`                                  | Number: HiDPI scale of output. Passed to pywm.                                                                                                                                                       |
| `round_scale`                           | `1.0`                                  | Number: Scale used for rounding positions and widths (i.e. if set equal to `output_scale`, windows will be positioned according to logical pixels, if set to 1 according to pixels). Passed to pywm. |
| `pywm`                                  |                                        | Dictionary: [pywm](https://github.com/jbuchermn/pywm) config, see possible keys below (is not updated on `Layout.update_config`)                                                                     |
| `pywm.xkb_model`                        |                                        | String: Keyboard model (`xkb`)                                                                                                                                                                       |
| `pywm.xkb_layout`                       | `us`                                   | String: Keyboard layout (`xkb`)                                                                                                                                                                      |
| `pywm.xkb_options`                      |                                        | String: Keyboard options (`xkb`)                                                                                                                                                                     |
| `pywm.enable_xwayland`                  | `False `                               | Boolean: Start `XWayland`                                                                                                                                                                            |
| `pywm.enable_output_manager`            | `True`                                 | Boolean: Enable the wayland protocol `xdg_output_manager_v1`                                                                                                                                         |
| `pywm.xcursor_theme`                    |                                        | String: `XCursor` theme                                                                                                                                                                              |
| `pywm.xcursor_size`                     | `24`                                   | Integer: `XCursor` size                                                                                                                                                                              |
| `pywm.focus_follows_mouse`              | `True`                                 | Boolean: `Focus` window upon mouse enter                                                                                                                                                             |
| `pywm.contstrain_popups_to_toplevel`    | `False`                                | Boolean: Try to keep popups contrained within their window                                                                                                                                           |
| `pywm.encourage_csd`                    | `True`                                 | Boolean: Encourage clients to show client-side-decorations (see `wlr_server_decoration_manager`)                                                                                                     |
|                                         |                                        |                                                                                                                                                                                                      |
| `anim_time`                             | `.3`                                   |                                                                                                                                                                                                      |
| `bar.bottom_texts`                      | `lambda: ["4", "5", "6"]`              |                                                                                                                                                                                                      |
| `bar.font`                              | `'Source Code Pro for Powerline'`      |                                                                                                                                                                                                      |
| `bar.font_size`                         | `12`                                   |                                                                                                                                                                                                      |
| `bar.height`                            | `20`                                   |                                                                                                                                                                                                      |
| `bar.top_texts`                         | `lambda: ["1", "2", "3"]`              |                                                                                                                                                                                                      |
| `blend_time`                            | `1.`                                   |                                                                                                                                                                                                      |
| `corner_radius`                         | `17.5`                                 |                                                                                                                                                                                                      |
| `gestures.lp_freq`                      | `60.`                                  |                                                                                                                                                                                                      |
| `gestures.lp_inertia`                   | `.8`                                   |                                                                                                                                                                                                      |
| `gestures.two_finger_min_dist`          | `.1`                                   |                                                                                                                                                                                                      |
| `gestures.validate_threshold`           | `.02`                                  |                                                                                                                                                                                                      |
| `greeter_user`                          | `'greeter'`                            |                                                                                                                                                                                                      |
| `grid.min_dist`                         | `.05`                                  |                                                                                                                                                                                                      |
| `grid.throw_ps`                         | `[1, 5, 15]`                           |                                                                                                                                                                                                      |
| `grid.time_scale`                       | `.3`                                   |                                                                                                                                                                                                      |
| `interpolation.size_adjustment`         | `.5`                                   |                                                                                                                                                                                                      |
| `key_bindings`                          | `lambda layout: []`                    |                                                                                                                                                                                                      |
| `launcher.gesture_factor`               | `200`                                  |                                                                                                                                                                                                      |
| `mod`                                   | `PYWM_MOD_LOGO`                        |                                                                                                                                                                                                      |
| `move.grid_m`                           | `2`                                    |                                                                                                                                                                                                      |
| `move.grid_ovr`                         | `0.2`                                  |                                                                                                                                                                                                      |
| `move_resize.gesture_factor`            | `4`                                    |                                                                                                                                                                                                      |
| `panel_dir`                             |                                        |                                                                                                                                                                                                      |
| `panels.launcher.cmd`                   |                                        |                                                                                                                                                                                                      |
| `panels.launcher.corner_radius`         | `0`                                    |                                                                                                                                                                                                      |
| `panels.launcher.h`                     | `0.8`                                  |                                                                                                                                                                                                      |
| `panels.launcher.w`                     | `0.8`                                  |                                                                                                                                                                                                      |
| `panels.lock.cmd`                       | `"alacritty -e newm-panel-basic lock"` |                                                                                                                                                                                                      |
| `panels.lock.corner_radius`             | `50`                                   |                                                                                                                                                                                                      |
| `panels.lock.h`                         | `0.5`                                  |                                                                                                                                                                                                      |
| `panels.lock.w`                         | `0.5`                                  |                                                                                                                                                                                                      |
| `panels.notifiers.cmd`                  |                                        |                                                                                                                                                                                                      |
| `power_times`                           | `[120, 300, 600]`                      |                                                                                                                                                                                                      |
| `resize.grid_m`                         | `3`                                    |                                                                                                                                                                                                      |
| `resize.grid_ovr`                       | `0.1`                                  |                                                                                                                                                                                                      |
| `resize.hyst`                           | `0.2`                                  |                                                                                                                                                                                                      |
| `swipe.gesture_factor`                  | `4`                                    |                                                                                                                                                                                                      |
| `swipe.grid_m`                          | `1`                                    |                                                                                                                                                                                                      |
| `swipe.grid_ovr`                        | `0.2`                                  |                                                                                                                                                                                                      |
| `swipe.lock_dist`                       | `0.01`                                 |                                                                                                                                                                                                      |
| `swipe_zoom.gesture_factor`             | `4`                                    |                                                                                                                                                                                                      |
| `swipe_zoom.grid_m`                     | `1`                                    |                                                                                                                                                                                                      |
| `swipe_zoom.grid_ovr`                   | `0.2`                                  |                                                                                                                                                                                                      |
| `swipe_zoom.hyst`                       | `0.2`                                  |                                                                                                                                                                                                      |
| `sys_backend_endpoints`                 | `[]`                                   |                                                                                                                                                                                                      |
| `view.corner_radius`                    | `12.5`                                 |                                                                                                                                                                                                      |
| `view.fullscreen_padding`               | `0`                                    |                                                                                                                                                                                                      |
| `view.padding`                          | `8`                                    |                                                                                                                                                                                                      |
| `view.send_fullscreen`                  | `True`                                 |                                                                                                                                                                                                      |
| `view.xwayland_handle_scale_clientside` | `False`                                |                                                                                                                                                                                                      |
| `wallpaper`                             |                                        |                                                                                                                                                                                                      |


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


## Status and limitations

This is the first release of newm. Therefore a lot of configurable behaviour, quality of documentation and the like is still missing. However the basic building blocks have been in use on my machine from the beginning (2018) continuously.

The most relevant functional limitation at the moment is missing support for multi-monitor setups. Apart from that see [pywm](https://github.com/jbuchermn/pywm) for known issues concerning certain applications.


## Panel

See [newm-panel-nwjs](https://github.com/jbuchermn/newm-panel-nwjs) for a different panel implementation (launcher, locker, notifiers) based on NW.js.
