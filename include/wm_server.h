#ifndef WM_SERVER_H
#define WM_SERVER_H

#include <wayland-server.h>
#include <wlr/backend.h>
#include <wlr/render/wlr_renderer.h>

struct wm_server{
    struct wl_display* wl_display;
    struct wl_event_loop* wl_event_loop;

    struct wlr_backend* wlr_backend;
    struct wlr_renderer* wlr_renderer;
    struct wlr_compositor* wlr_compositor;
    struct wlr_data_device_manager* wlr_data_device_manager;

    struct wl_listener new_input;
    struct wl_list wm_seats; // wm_seat::link
};

void wm_server_init(struct wm_server* server);
void wm_server_destroy(struct wm_server* server);

#endif
