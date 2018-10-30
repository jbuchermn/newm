#include <assert.h>
#include <stdlib.h>
#include <wayland-server.h>
#include <wlr/backend.h>
#include <wlr/backend/headless.h>
#include <wlr/backend/multi.h>
#include <wlr/types/wlr_compositor.h>
#include <wlr/types/wlr_data_device.h>
#include <wlr/config.h>
#include <wlr/render/wlr_renderer.h>
#include <wlr/util/log.h>

#include "wm_server.h"
#include "wm_seat.h"


/*
 * Callbacks
 */
static void handle_new_input(struct wl_listener* listener, void* data){
    struct wlr_input_device* input_device = data;
    struct wm_server* server = wl_container_of(listener, server, new_input);

    /* For now, only one seat */
    if(wl_list_empty(&server->wm_seats)){
        struct wm_seat* seat = calloc(1, sizeof(struct wm_seat));
        wm_seat_init(seat, server);
        wl_list_insert(&server->wm_seats, &seat->link);
        wlr_log(WLR_DEBUG, "New seat");
    }

    struct wm_seat* seat;
    wl_list_for_each(seat, &server->wm_seats, link){
        wm_seat_add_input_device(seat, input_device);
    }

}

/*
 * Class implementation
 */
void wm_server_init(struct wm_server* server){
    /* Fields */
    wl_list_init(&server->wm_seats);

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

    /* Handlers */
    server->new_input.notify = handle_new_input;
    wl_signal_add(&server->wlr_backend->events.new_input, &server->new_input);
}

void wm_server_destroy(struct wm_server* server){
    wl_display_destroy_clients(server->wl_display);
    wl_display_destroy(server->wl_display);
}
