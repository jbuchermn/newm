#ifndef WM_VIEW_H
#define WM_VIEW_H

#include <stdbool.h>
#include <wayland-server.h>
#include <wlr/types/wlr_xdg_shell.h>

struct wm_view{
    struct wl_list link;  // wm_server::wm_views
    struct wm_server* wm_server;

    bool mapped;

    int x;
    int y;
    int width;
    int height;
    double scale;

    struct wlr_xdg_surface* wlr_xdg_surface;

    struct wl_listener map;
    struct wl_listener unmap;
    struct wl_listener destroy;
    struct wl_listener new_popup;
};

void wm_view_init(struct wm_view* view, struct wm_server* server, struct wlr_xdg_surface* surface);
void wm_view_destroy(struct wm_view* view);

void wm_view_update(struct wm_view* view, struct timespec when);

#endif
