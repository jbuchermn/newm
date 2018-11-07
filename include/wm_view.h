#ifndef WM_VIEW_H
#define WM_VIEW_H

#include <stdbool.h>
#include <wayland-server.h>
#include <wlr/types/wlr_xdg_shell.h>
#include <wlr/types/wlr_xdg_decoration_v1.h>

struct wm_view_decoration {
    struct wl_list link; // wm_server::wm_view_decorations

    struct wlr_xdg_toplevel_decoration_v1* wlr_xdg_toplevel_decoration;

    struct wl_listener request_mode;
    struct wl_listener destroy;
};

void wm_view_decoration_init(struct wm_view_decoration* deco, struct wlr_xdg_toplevel_decoration_v1* wlr_deco);
void wm_view_decoration_destroy(struct wm_view_decoration* deco);

struct wm_view {
    struct wl_list link;  // wm_server::wm_views
    struct wm_server* wm_server;

    const char* title;
    const char* app_id;

    bool mapped;
    double display_x;
    double display_y;
    double display_width;
    double display_height;

    struct wlr_xdg_surface* wlr_xdg_surface;

    struct wl_listener map;
    struct wl_listener unmap;
    struct wl_listener destroy;
    struct wl_listener new_popup;
};

void wm_view_init(struct wm_view* view, struct wm_server* server, struct wlr_xdg_surface* surface);
void wm_view_destroy(struct wm_view* view);

void wm_view_update(struct wm_view* view, struct timespec when);
uint32_t wm_view_request_size(struct wm_view* view, int width, int height);
void wm_view_get_size(struct wm_view* view, int* width, int* height);

#endif
