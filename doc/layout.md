### Layout functions

To configure specific behaviour, a `Layout` object is passed to the `key_bindings` config value. The following methods
are relevant in general - more detailed config on this to follow.

```py
class Layout:
    """
    API to be used for configuration
    1. Getters
    """
    def get_active_workspace(self) -> Workspace:
    def tiles(self, workspace: Optional[Workspace]=None) -> list[View]:
    def floats(self, workspace: Optional[Workspace]=None) -> list[View]:
    def panels(self, workspace: Optional[Workspace]=None) -> list[View]:
    def views(self, workspace: Optional[Workspace]=None) -> list[View]:
    def find_focused_view(self) -> Optional[View]:

    """
    2. General purpose methods
    """
    def update_config(self) -> None:
    def ensure_locked(self, anim: bool=True, dim: bool=False) -> None:
    def terminate(self) -> None:

    """
    3. Change global or workspace state / move viewpoint
    """
    def enter_launcher_overlay(self) -> None:
    def toggle_overview(self, only_active_workspace: bool=False) -> None:
    def toggle_fullscreen(self, defined_state: Optional[bool] = None) -> None:
    def basic_move(self, delta_i: int, delta_j: int) -> None:
    def basic_scale(self, delta_s: int) -> None:
    """
    4. Change focus
    """
    def focus_view(self, view: View) -> None:
    def move_in_stack(self, delta: int) -> None:
    def move(self, delta_i: int, delta_j: int) -> None:
    def move_next_view(self, dv: int=1, active_workspace: bool=True) -> None:
    def move_workspace(self, ds: int=1) -> None:

    """
    5. Change focused view
    """
    def close_focused_view(self) -> None:
    def toggle_focused_view_floating(self) -> None:
    def change_focused_view_workspace(self, ds: int=1) -> None:
    def move_focused_view(self, di: int, dj: int) -> None:
    def resize_focused_view(self, di: int, dj: int) -> None:
```
