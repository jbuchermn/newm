# NeWM - PyWM reference implementation

## ToDo

- MoveResizeOverlay
    - Trigger move without lifting finger first (works for resize)
    - Block used tiles
- Clean up get_view_state --> possibly update_view_state_in_place(...)


## Backlog

- NW.js bars (make it optional!)
- SwipeOverlays / MoveResizeOverlays: Improve momenteum handling / grid snapping / Use momentum as basis for animation duration?

- Titles during "far-away" view
- htop / cmatrix or similar background / screensaver
- Autoplace the first couple of windows more like i3 (i.e. resizing existing windows / tiling)
- Configurable
    - Starter panel (follow XDG!)
    - TODOs in PyWM
    - Key mappings
- Performance issues on resizing Spotify / similar XWayland apps
