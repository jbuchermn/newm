#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <stdlib.h>
#include <wayland-server.h>
#include <wlr/backend.h>
#include <wlr/backend/headless.h>
#include <wlr/backend/multi.h>
#include <wlr/types/wlr_compositor.h>
#include <wlr/types/wlr_data_device.h>
#include <wlr/types/wlr_output.h>
#include <wlr/config.h>
#include <wlr/render/wlr_renderer.h>
#include <wlr/util/log.h>

#include "wm_server.h"
#include "wm_seat.h"
#include "wm_view.h"


/*
 * Callbacks
 */
static void handle_new_input(struct wl_listener* listener, void* data){
    struct wm_server* server = wl_container_of(listener, server, new_input);
    struct wlr_input_device* input_device = data;

    wm_seat_add_input_device(server->wm_seat, input_device);
}

static void handle_new_output(struct wl_listener* listener, void* data){
    struct wm_server* server = wl_container_of(listener, server, new_output);
    struct wlr_output* output = data;

    wm_layout_add_output(server->wm_layout, output);
}

static void handle_new_xdg_surface(struct wl_listener* listener, void* data){
    struct wm_server* server = wl_container_of(listener, server, new_xdg_surface);
    struct wlr_xdg_surface* surface = data;

    if(surface->role != WLR_XDG_SURFACE_ROLE_TOPLEVEL){
        return;
    }

    struct wm_view* view = calloc(1, sizeof(struct wm_view));
    wm_view_init(view, server, surface);

    wl_list_insert(&server->wm_views, &view->link);
}

/*
 * Class implementation
 */
void wm_server_init(struct wm_server* server){
    wl_list_init(&server->wm_views);

    /* Wayland and wlroots resources */
    server->wl_display = wl_display_create();
    assert(server->wl_display);

    server->wl_event_loop = wl_display_get_event_loop(server->wl_display);
    assert(server->wl_event_loop);

    server->wlr_backend = wlr_backend_autocreate(server->wl_display, NULL);
    assert(server->wlr_backend);

    server->wlr_renderer = wlr_backend_get_renderer(server->wlr_backend);
    assert(server->wlr_renderer);

    wlr_renderer_init_wl_display(server->wlr_renderer, server->wl_display);

    server->wlr_compositor = wlr_compositor_create(server->wl_display, server->wlr_renderer);
    assert(server->wlr_compositor);

    server->wlr_data_device_manager = wlr_data_device_manager_create(server->wl_display);
    assert(server->wlr_data_device_manager);

    server->wlr_xdg_shell = wlr_xdg_shell_create(server->wl_display);
    assert(server->wlr_xdg_shell);

    /* Children */
    server->wm_layout = calloc(1, sizeof(struct wm_layout));
    wm_layout_init(server->wm_layout, server);

    server->wm_seat = calloc(1, sizeof(struct wm_seat));
    wm_seat_init(server->wm_seat, server, server->wm_layout);

    /* Handlers */
    server->new_input.notify = handle_new_input;
    wl_signal_add(&server->wlr_backend->events.new_input, &server->new_input);

    server->new_output.notify = handle_new_output;
    wl_signal_add(&server->wlr_backend->events.new_output, &server->new_output);

    server->new_xdg_surface.notify = handle_new_xdg_surface;
    wl_signal_add(&server->wlr_xdg_shell->events.new_surface, &server->new_xdg_surface);
}

void wm_server_destroy(struct wm_server* server){
    wl_display_destroy_clients(server->wl_display);
    wl_display_destroy(server->wl_display);
}
