# NeWM - PyWM reference implementation

## ToDo

- Get rid of min_i, min_j, .. in state and reset_extent / rescale / ...
- Move PinchOverlay towards moving and resizing functionality -> get rid of Ctrl-Mod and Shift-Mod
- Swipe Overlay: Bouncy overswipe effect (i.e. not a whole tile)
- Clean up new state handling newm-side and fix bugs (animations / on_finish callbacks / queue animations / ...)

- Starter panel
- Battery warning
- Unified handling of stoppable threads spawned by layout.py


## Backlog

- Center windows of 1x2 or 2x1 in regular view and overview
- Improve "find next window" logic on Alt-hjkl
- Titles during "far-away" view
- Move Ctrl-Mod and Shift-Mod to an i3-like behaviour only on currently visible windows
- Useful to zoom out beyond scale=2 or 3?
- Autoplace the first couple of windows more like i3 (i.e. resizing existing windows / tiling)
- htop / cmatrix or similar background / screensaver
