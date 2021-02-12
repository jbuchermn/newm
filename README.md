# NeWM - PyWM reference implementation

## ToDo

- Better state handling newm-side
    - up_state out of layout
    - in_progres into state
    - GIMP sizing
    - Size during / after animation
    - Launcher panel

- Move PinchOverlay towards moving and resizing functionality -> get rid of Ctrl-Mod and Shift-Mod
- Starter panel
- Battery warning
- Swipe Overlay: Bouncy overswipe effect (i.e. not a whole tile)
- Unified handling of stoppable threads spawned by layout.py


## Backlog

- Center windows of 1x2 or 2x1 in regular view and overview
- Improve "find next window" logic on Alt-hjkl
- Titles during "far-away" view
- Move Ctrl-Mod and Shift-Mod to an i3-like behaviour only on currently visible windows
- Useful to zoom out beyond scale=2 or 3?
- Autoplace the first couple of windows more like i3 (i.e. resizing existing windows / tiling)
- htop / cmatrix or similar background / screensaver
