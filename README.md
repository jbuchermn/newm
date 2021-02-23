# NeWM - PyWM reference implementation

## Current

- All animations --> deferred (aware that current state is not necessary start state)
- Never reject gestures in MoveResizeOverlay

- Block animations during overlay / occasional bug when opening window and moving cursor meanwhile
- New / Destroyed views during OverviewOverlay (and other overlays) 

- Generalized used tiles handling / free tiles finding / ...
- MoveResizeOverlay: Block used tiles
- Fix place_initial

- move() / resize() functions with keybindings
- SwipeOverlays / MoveResizeOverlays: Improve momentum handling / grid snapping / Use momentum as basis for animation duration?


## Backlog

- Configurable keybindings
- Configurable Top / Bottom bar
- Configurable SysBackend

- Install guide and tests on other machines

- NW.js bars (make it optional!)
- Follow XDG for entries in starter panel

- Performance issues on resizing Spotify / similar XWayland apps

- Titles during "far-away" view
- Autoplace the first couple of windows more like i3 (i.e. resizing existing windows / tiling)
