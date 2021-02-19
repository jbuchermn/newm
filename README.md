# NeWM - PyWM reference implementation

## ToDo

- Alacritty startup placement
- SwipeOverlays / MoveResizeOverlays: Improve momenteum handling / grid snapping / Use momentum as basis for animation duration?
- MoveResizeOverlay
    - Trigger move without lifting finger first (works for resize)
    - Adjust viewpoint during move
    - Hide cursor during move / resize (alternatively move it)
    - Start gesture even during anim_block
    - Block already used tiles

- NW.js bars (make it optional!)
- Many windows open (especially with e.g. Spotify - XWayland?) -> resize during animation slow


## Backlog

- Titles during "far-away" view
- htop / cmatrix or similar background / screensaver
- Autoplace the first couple of windows more like i3 (i.e. resizing existing windows / tiling)
- Configurable
    - Starter panel (follow XDG!)
    - TODOs in PyWM
    - Key mappings
