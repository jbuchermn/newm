#ifndef WM_SERVER_H
#define WM_SERVER_H

#include <wayland-server.h>
#include <wlr/backend.h>
#include <wlr/render/wlr_renderer.h>
#include <wlr/types/wlr_xdg_shell.h>
#include <wlr/types/wlr_server_decoration.h>
#include <wlr/types/wlr_xdg_decoration_v1.h>

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
    struct wlr_server_decoration_manager* wlr_server_decoration_manager;
    struct wlr_xdg_decoration_manager_v1* wlr_xdg_decoration_manager;
#ifdef PYWM_XWAYLAND
    struct wlr_xwayland* wlr_xwayland;
    struct wlr_xcursor_manager* wlr_xcursor_manager;
#endif

    struct wm_seat* wm_seat;
    struct wm_layout* wm_layout;
    struct wl_list wm_views;  // wm_view::link
    struct wl_list wm_widgets;  // wm_widget::link

    struct wl_listener new_input;
    struct wl_listener new_output;
    struct wl_listener new_xdg_surface;
    struct wl_listener new_server_decoration;
    struct wl_listener new_xdg_decoration;
#ifdef PYWM_XWAYLAND
    struct wl_listener xwayland_ready;
    struct wl_listener new_xwayland_surface;
#endif
};

void wm_server_init(struct wm_server* server);
void wm_server_destroy(struct wm_server* server);

void wm_server_surface_at(struct wm_server* server, double at_x, double at_y, 
        struct wlr_surface** result, double* result_sx, double* result_sy);
struct wm_view* wm_server_view_for_surface(struct wm_server* server, struct wlr_surface* surface);

/* passes ownership to caller, no need to unregister, simply destroy */
struct wm_widget* wm_server_create_widget(struct wm_server* server);

#endif
