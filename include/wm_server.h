#ifndef WM_SERVER_H
#define WM_SERVER_H

#include <wayland-server.h>
#include <wlr/backend.h>
#include <wlr/render/wlr_renderer.h>
#include <wlr/types/wlr_xdg_shell.h>

struct wm_seat;
struct wm_layout;

struct wm_server{
    struct wl_display* wl_display;
    struct wl_event_loop* wl_event_loop;

    struct wlr_backend* wlr_backend;
    struct wlr_compositor* wlr_compositor;
    struct wlr_renderer* wlr_renderer;
    struct wlr_data_device_manager* wlr_data_device_manager;
    struct wlr_xdg_shell* wlr_xdg_shell;

    struct wm_seat* wm_seat;
    struct wm_layout* wm_layout;
    struct wl_list wm_views;  // wm_view::link

    struct wl_listener new_input;
    struct wl_listener new_output;
    struct wl_listener new_xdg_surface;
};

void wm_server_init(struct wm_server* server);
void wm_server_destroy(struct wm_server* server);

void wm_server_surface_at(struct wm_server* server, double at_x, double at_y, 
        struct wlr_surface** result, double* result_sx, double* result_sy);

#endif
