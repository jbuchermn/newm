### Config: Basic

These values are mostly passed to [pywm](https://github.com/jbuchermn/pywm) and configure basic behaviour needed c-side.

| Configuration key                    | Default value | Description                                                                                             |
| ------------------------------------ | ------------- | --------------------------------------------------------------------------------------------------------|
| `outputs`                            |               | List of dictionaries: Output configuration (see next lines)                                             |
| `output.name`                        | `""`          | String: Name of output to attach config to actual output                                                |
| `output.scale`                       | `1.0`         | Number: HiDPI scale of output                                                                           |
| `output.width`                       | `0`           | Integer: Output width (or zero to use preferred)                                                        |
| `output.height`                      | `0`           | Integer: Output height (or zero to use preferred)                                                       |
| `output.mHz`                         | `0`           | Integer: Output refresh rate in milli Hertz (or zero to use preferred)                                  |
| `output.pos_x`                       | `None`        | Integer: Output position x in layout (or None to be placed automatically)                               |
| `output.pos_y`                       | `None`        | Integer: Output position y in layout (or None to be placed automatically)                               |
| `output.anim`                        | `True`        | Bool: Enable or disable most animations on this output (useful for virtual outputs)                     |
| `output.background.path`             |               | String: Optionally specify wallpaper for this output (overrides `background.path`)                      |
| `output.background.anim`             | `True`        | Bool: Optionally disable movements of the background (overrides `output.anim` and `background.anim`)    |
| `pywm`                               |               | Dictionary: [pywm](https://github.com/jbuchermn/pywm) config, see possible keys below                   |
| `pywm.enable_xwayland`               | `False`       | Boolean: Start `XWayland`                                                                               |
| `pywm.xkb_model`                     |               | String: Keyboard model (`xkb`)                                                                          |
| `pywm.xkb_layout`                    |               | String: Keyboard layout (`xkb`)                                                                         |
| `pywm.xkb_variant`                   |               | String: Keyboard variant (`xkb`)                                                                        |
| `pywm.xkb_options`                   |               | String: Keyboard options (`xkb`)                                                                        |
| `pywm.outputs`                       |               | List of dicts: Output configuration (see next lines)                                                    |
| `pywm.output.name`                   | `""`          | String: Name of output to attach config to actual output                                                |
| `pywm.output.scale`                  | `1.0`         | Number: HiDPI scale of output                                                                           |
| `pywm.output.width`                  | `0`           | Integer: Output width (or zero to use preferred)                                                        |
| `pywm.output.height`                 | `0`           | Integer: Output height (or zero to use preferred)                                                       |
| `pywm.output.mHz`                    | `0`           | Integer: Output refresh rate in milli Hertz (or zero to use preferred)                                  |
| `pywm.output.pos_x`                  | `None`        | Integer: Output position x in layout (or None to be placed automatically)                               |
| `pywm.output.pos_y`                  | `None`        | Integer: Output position y in layout (or None to be placed automatically)                               |
| `pywm.xcursor_theme`                 |               | String: `XCursor` theme (if not set, read from; if set, exported to `XCURSOR_THEME`)                    |
| `pywm.xcursor_size`                  | `24`          | Integer: `XCursor` size (if not set, read from; if set, exported to `XCURSOR_SIZE`)                     |
| `pywm.tap_to_click`                  | `True`        | Boolean: On touchpads use tap for click enter                                                           |
| `pywm.natural_scroll`                | `True`        | Boolean: On touchpads use natural scrolling enter                                                       |
| `pywm.focus_follows_mouse`           | `True`        | Boolean: `Focus` window upon mouse enter                                                                |
| `pywm.contstrain_popups_to_toplevel` | `False`       | Boolean: Try to keep popups contrained within their window                                              |
| `pywm.encourage_csd`                 | `True`        | Boolean: Encourage clients to show client-side-decorations (see `wlr_server_decoration_manager`)        |
| `pywm.debug`                         | `False`       | Boolean: Loglevel debug plus output debug information to stdout on every F1 press                       |
| `pywm.texture_shaders`               | `basic`       | String: Shaders to use for texture rendering (see `src/wm/shaders/texture`)                             |
| `pywm.renderer_mode`                 | `pywm`        | String: Renderer mode, `pywm` (enable pywm renderer, and therefore blur), `wlr` (disable pywm renderer) |

### Config: General appearance

Some basic appearence and animation related configuration:

| Configuration key               | Default value | Description                                                                                                                                                                        |
| ------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `background.path`               |               | String: Path to background image (replaces obsolete `wallpaper`)                                                                                                                   |
| `background.time_scale`         | `0.15`        | Number: Time scale of background movement                                                                                                                                          |
| `background.anim`               | `True`        | Bool: Prevent (`False`) background movement                                                                                                                                        |
| `blend_time`                    | `1.`          | Number: Time in seconds to blend in and out (at startup and shutdown)                                                                                                              |
| `anim_time`                     | `.3`          | Number: Timescale of all animations in seconds                                                                                                                                     |
| `corner_radius`                 | `17.5`        | Number: Radius of blacked out corners of display (0 to disable)                                                                                                                    |
| `view.corner_radius`            | `12.5`        | Number: Corner radius of views (0 to disable)                                                                                                                                      |
| `view.padding`                  | `8`           | Number: Padding around windows in normal mode (pixels)                                                                                                                             |
| `view.fullscreen_padding`       | `0`           | Number: Padding around windows when they are in fullscreen (pixels)                                                                                                                |
| `interpolation.size_adjustment` | `.5`          | Number: When window size adjustments of windows (slow) happen during gestures and animations, let them take place at the middle (`.5`) or closer to start / end (`.1` / `.9` e.g.) |

A very basic server-side decoration implementation is available (unicolor rounded corners border around a view). This will be displayed on views requesting SSDs and floating views.

| Configuration key               | Default value | Description                            |                                                                                                                                            |
| ------------------------------- | ------------- | -------------------------------------- |
|`view.ssd.enabled`               |`True`         | Enable SSD drawing                     |
|`view.ssd.color`                 |`'#BEBEBEFF'`  | Color of the border                    |
|`view.ssd.width`                 |`2`            | Width in pixels                        |

Also a border highlight can be displayed around focused windows:

| Configuration key               | Default value | Description                            |                                                                                                                                            |
| ------------------------------- | ------------- | -------------------------------------- |
|`focus.enabled`                  |`True`         | Enable the fous highlight              |
|`focus.color`                    |`'#19CEEB55'`  | Color of the focus highlight           |
|`focus.distance`                 |`4`            | Width of the border                    |
|`focus.width`                    |`2`            | Distance to view                       |
|`focus.animate_on_change`        |`False`        | Show an animation when focus changes   |
|`focus.anim_time`                |`0.3`          | Timescale of this animation            |

### Config: Behaviour, keys and gestures

The most important configuration options with regard to behaviour are `mod` and `key_bindings`; see below for them and some more detailed ones.

| Configuration key        | Default value         | Description                                                                                                                                                                                                                                                                                                        |
| ------------------------ | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `key_bindings`           | `lambda layout: []`   | Key bindings as array, see `default_config.py`, `layout.py` and [dotfiles](https://github.com/jbuchermn/dotfiles/blob/master/newm/home/.config/newm/config.py))                                                                                                                                                    |
| `view.send_fullscreen`   | `True`                | Let clients know when they are set to fullscreen (which leads to them adjusting, e.g. YouTube fullscreen)                                                                                                                                                                                                          |
| `view.accept_fullscreen` | `True`                | Set a view to fullscreen, if it requests so, setting this to `False` will leave a view in its tile while the view thinks it is in fullscreen mode, which might be desirable                                                                                                                                        |
| `view.floating_min_size` | `True`                | Try to open floating views in their minimal size instead of their preferred one. This doesn't always work as not all view report minimal size                                                                                                                                                                      |
| `view.border_ws_switch`  | `10.`                 | Amount of pixels a view, which is currently being moved, has to reach into a new output to be switched over to this new output                                                                                                                                                                                     |
| `view.rules`             | `lambda view: None`   | Function: Set rules based on a view (e.g. based on `view.app_id`): Return a dict with all rules set (see below for possible rules).                                                                                                                                                                                |
| `lock_on_wakeup`         | `True`                | Lock screen after wake up is detected (does not work as well as locking on systemd sleep)                                                                                                                                                                                                                          |
| `greeter_user`           | `'greeter'`           | Relevant if newm is run as login display manager, username used for `greetd`                                                                                                                                                                                                                                       |
| `on_startup`             | `lambda: None`        | Function called when the compositor has started, use to run certain things using `os.system("... &")`                                                                                                                                                                                                              |
| `on_reconfigure`         | `lambda: None`        | Function called when the compositor has reloaded the config                                                                                                                                                                                                                                                        |
| `synchronous_update`     | `lambda: None`        | Function: called once per frame, can be used to e.g. update backlight dynamically. Be careful, will block the compositor.                                                                                                                                                                                          |
| `view.debug_scaling`     | `False`               | Debug sclaing of views - if you think views look blurry, this outputs potential issues where logical size and size on the display do not match                                                                                                                                                                     |
| `enable_unlock_command`  | `False`               | Boolean: Enable `newm-cmd unlock` to unlock the compositor from second tty if lock screen breaks.                                                                                                                                                                                                                  |
| `energy.idle_callback`   | `lambda event: None`  | Callback called with events `"lock", "idle", "idle-lock", "idle-presuspend", "idle-suspend", "active", "sleep", "wakeup"` to e.g. adjust backlight. See [layout.py](https://github.com/jbuchermn/newm/newm/layout.py) and [default_config.py](https://github.com/jbuchermn/newm/newm/default_config.py)            |
| `energy.idle_times`      | `[120, 300, 600]`     | Times to dim, lock and suspend, empty list disables energy management.                                                                                                                                                                                                                                             |
| `energy.suspend_command` | `"systemctl suspend"` | Command called to suspend after `power_times[2] has passed`.                                                                                                                                                                                                                                                       |

The following rules can be used in `view.rules`:
- `opacity` (e.g. `lambda view: {'opacity': 0.8 }`): Set transparency of view.
- `blur` (e.g. `lambda view: { 'blur': { 'raidus': 5, passes: 2 }}`): Apply background Kawase blur with radius and passes.
- `float`, `float_size` (oprional) and `float_pos` (optional), e.g. `lambda view: { 'float': True, 'float_size': (300, 300), 'float_pos': (0.5, 0.5)}`: Always open certain views floating, possibly supplying size and position.

Gestures are configured by a lot of numeric parameters; these are structured by the different gesture kinds (swipe to move, swipe to zoom, move, resize)
as well as some general ones (`gestures` and `grid`). The best way is to experiment with these and hot-reload the configuration (by default `M-C`). Also `grid.py` acts as a
plot script when (`grid.debug`) is enabled.

| Configuration key              | Default value |
| ------------------------------ | ------------- |
| `gestures.lp_freq`             | `60.`         |
| `gestures.lp_inertia`          | `.8`          |
| `gestures.two_finger_min_dist` | `.1`          |
| `gestures.validate_threshold`  | `.02`         |
| `grid.debug`                   | `False`       |
| `grid.min_dist`                | `.05`         |
| `grid.throw_ps`                | `[1, 5, 15]`  |
| `grid.time_scale`              | `.3`          |
| `resize.grid_m`                | `3`           |
| `resize.grid_ovr`              | `0.1`         |
| `resize.hyst`                  | `0.2`         |
| `swipe.gesture_factor`         | `4`           |
| `swipe.grid_m`                 | `1`           |
| `swipe.grid_ovr`               | `0.2`         |
| `swipe.lock_dist`              | `0.01`        |
| `swipe_zoom.gesture_factor`    | `4`           |
| `swipe_zoom.grid_m`            | `1`           |
| `swipe_zoom.grid_ovr`          | `0.2`         |
| `swipe_zoom.hyst`              | `0.2`         |
| `move.grid_m`                  | `3`           |
| `move.grid_ovr`                | `0.2`         |
| `move_resize.gesture_factor`   | `2`           |

Configurable actions on keybindings can be any function calls on `layout`. Check the class `Layout` and [layout](layout.md) for details.

### Config: Top and bottom bars

The top and bottom bars are visible during the zoom-out ("Overview") mode. Configure font and texts (for an example see [dotfiles](https://github.com/jbuchermn/dotfiles/blob/master/newm/home/.config/newm/config.py))

| Configuration key  | Default value                     | Description                                            |
| ------------------ | --------------------------------- | ------------------------------------------------------ |
| `bar.enabled`      | `True`                            | Show newm bars (set to `False` in order to use waybar) |
| `bar.font`         | `'Source Code Pro for Powerline'` | Font name used in both bars                            |
| `bar.font_size`    | `12`                              | Font size used in both bars                            |
| `bar.height`       | `20`                              | Pixel height of both bars                              |
| `bar.top_texts`    | `lambda: ["1", "2", "3"]`         | Function called each time top bar is rendered          |
| `bar.bottom_texts` | `lambda: ["4", "5", "6"]`         | Function called each time bottom bar is rendererd      |

### Config: Panels

**Warning - This functionality is going to need a rewrite in v0.3 - websocket connection is not here to stay and layer shell makes much of this config unnecessary**

Panels in this context means the UI elements you interact with to

- Launch an application from a menu (launcher)
- Unlock the screen (locker)
- Get information on changed volume etc (notifiers)

These are in general separate apps and can be developed independently of newm; they are started by newm and establish a connection to the compositor via websockets.

By default **newm_panel_basic** is included, where the first two of these are implemented as terminal applications in a very basic manner.
See below for a different implementation using NW.js.

| Configuration key                | Default value                              | Description                                                                          |
| -------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------ |
| `panels.launcher.cmd`            | `"alacritty -e newm-panel-basic launcher"` | Command to start launcher panel                                                      |
| `panels.launcher.cwd`            |                                            | Directory to start launcher panel in                                                 |
| `panels.launcher.corner_radius`  | `0`                                        | Launcher panel: corner radius (pixel)                                                |
| `panels.launcher.h`              | `0.8`                                      | Launcher panel: height (`1.0` is full height)                                        |
| `panels.launcher.w`              | `0.8`                                      | Launcher panel: width (`1.0` is full width)                                          |
| `panels.launcher.gesture_factor` | `200`                                      | Higher number means less movement with 5 fingers is necessary to open laucnher panel |
| `panels.lock.cmd`                | `"alacritty -e newm-panel-basic lock"`     | Command to start lock panel                                                          |
| `panels.lock.cwd`                |                                            | Directory to start lock panel in                                                     |
| `panels.lock.corner_radius`      | `50`                                       | Lock panel: corner radius (pixel)                                                    |
| `panels.lock.h`                  | `0.6`                                      | Lock panel: height (`1.0` is full height)                                            |
| `panels.lock.w`                  | `0.7`                                      | Lock panel: width (`1.0` is full width)                                              |
| `panels.notifiers.cmd`           |                                            | Command to start notifiers panel                                                     |
| `panels.notifiers.cwd`           |                                            | Directory to start notifiers panel in                                                |
| `panels.notifiers.h`             | `0.3`                                      | Notifiers panel: height (`1.0` is full height)                                       |
| `panels.notifiers.w`             | `0.2`                                      | Notifiers panel: width (`1.0` is full width)                                         |

The basic launcher panel is configured using `~/.config/newm/launcher.py`, e.g.

```py
entries = {
    "chromium": "chromium --enable-features=UseOzonePlatform --ozone-platform=wayland",
    "alacritty": "alacritty"
}
shortcuts = {
    1: ("chromium", "chromium --enable-features=UseOzonePlatform --ozone-platform=wayland"),
    2: ("alacritty", "alacritty")
}
```

provides ways to start chromium and alacritty either by typing their names, or by using the keys 1 and 2 when the launcher is open.
