# NeWM - PyWM reference implementation

## Current

- All animations --> deferred (aware that current state is not necessary start state)
- Block animations during overlay
- print to log with file, line, severity

- MoveResizeOverlay: Block used tiles
- move() / resize() functions with keybindings
- SwipeOverlays / MoveResizeOverlays: Improve momentum handling / grid snapping / Use momentum as basis for animation duration?

- Configurable keybindings
- Configurable Top / Bottom bar
- Configurable SysBackend

- Install guide and tests on other machines

## Backlog

- NW.js bars (make it optional!)
- Follow XDG for entries in starter panel

- Performance issues on resizing Spotify / similar XWayland apps

- Titles during "far-away" view
- Autoplace the first couple of windows more like i3 (i.e. resizing existing windows / tiling)
