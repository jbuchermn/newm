#ifndef WM_VIEW_H
#define WM_VIEW_H

#include <stdbool.h>
#include <wayland-server.h>
#include <wlr/types/wlr_xdg_shell.h>

struct wm_view{
    struct wl_list link;  // wm_server::wm_views

    bool mapped;
    int x;
    int y;

    struct wlr_xdg_surface* wlr_xdg_surface;

    struct wl_listener map;
    struct wl_listener unmap;
    struct wl_listener destroy;
};

void wm_view_init(struct wm_view* view, struct wlr_xdg_surface* surface);
void wm_view_destroy(struct wm_view* view);

#endif
