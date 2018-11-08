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
#include <wlr/types/wlr_linux_dmabuf_v1.h>
#include <wlr/util/log.h>

#include "wm/wm_server.h"
#include "wm/wm_seat.h"
#include "wm/wm_view.h"
#include "wm/wm_layout.h"


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

static void handle_new_xdg_decoration(struct wl_listener* listener, void* data){
    struct wm_server* server = wl_container_of(listener, server, new_xdg_decoration);
    struct wlr_xdg_toplevel_decoration_v1* wlr_deco = data;

    struct wm_view_decoration* deco = calloc(1, sizeof(struct wm_view_decoration));
    wm_view_decoration_init(deco, wlr_deco);

    wl_list_insert(&server->wm_view_decorations, &deco->link);
}

/*
 * Class implementation
 */
void wm_server_init(struct wm_server* server){
    wl_list_init(&server->wm_views);
    wl_list_init(&server->wm_view_decorations);

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
    wlr_linux_dmabuf_v1_create(server->wl_display, server->wlr_renderer);

    server->wlr_compositor = wlr_compositor_create(server->wl_display, server->wlr_renderer);
    assert(server->wlr_compositor);

    server->wlr_data_device_manager = wlr_data_device_manager_create(server->wl_display);
    assert(server->wlr_data_device_manager);

    server->wlr_xdg_shell = wlr_xdg_shell_create(server->wl_display);
    assert(server->wlr_xdg_shell);

    server->wlr_xdg_decoration_manager = wlr_xdg_decoration_manager_v1_create(server->wl_display);
    assert(server->wlr_xdg_decoration_manager);


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

    server->new_xdg_decoration.notify = handle_new_xdg_decoration;
    wl_signal_add(&server->wlr_xdg_decoration_manager->events.new_toplevel_decoration, &server->new_xdg_decoration);
}

void wm_server_destroy(struct wm_server* server){
    wl_display_destroy_clients(server->wl_display);
    wl_display_destroy(server->wl_display);
}

void wm_server_surface_at(struct wm_server* server, double at_x, double at_y, 
        struct wlr_surface** result, double* result_sx, double* result_sy){
    struct wm_view* view;
    wl_list_for_each(view, &server->wm_views, link){
        int width;
        int height;
        wm_view_get_size(view, &width, &height);

        double scale_x = view->display_width/width;
        double scale_y = view->display_height/height;

        int view_at_x = round((at_x - view->display_x) / scale_x);
        int view_at_y = round((at_y - view->display_y) / scale_y);

        double sx;
        double sy;
        struct wlr_surface* surface = wlr_xdg_surface_surface_at(view->wlr_xdg_surface, view_at_x, view_at_y, &sx, &sy);

        if(surface){
            *result = surface;
            *result_sx = sx;
            *result_sy = sy;
            return;
        }
    }

    *result = NULL;
}