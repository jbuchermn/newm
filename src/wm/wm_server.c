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
#include <wlr/types/wlr_xcursor_manager.h>
#include <wlr/util/log.h>
#include <wlr/xwayland.h>

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

    wlr_xdg_surface_ping(surface);

    struct wm_view* view = calloc(1, sizeof(struct wm_view));
    wm_view_init_xdg(view, server, surface);

    wl_list_insert(&server->wm_views, &view->link);
}

static void handle_new_xwayland_surface(struct wl_listener* listener, void* data){
    struct wm_server* server = wl_container_of(listener, server, new_xwayland_surface);
    struct wlr_xwayland_surface* surface = data;

    wlr_xwayland_surface_ping(surface);

    struct wm_view* view = calloc(1, sizeof(struct wm_view));
    wm_view_init_xwayland(view, server, surface);

    wl_list_insert(&server->wm_views, &view->link);

}

static void handle_new_server_decoration(struct wl_listener* listener, void* data){
    /* struct wm_server* server = wl_container_of(listener, server, new_xdg_decoration); */
    /* struct wlr_server_decoration* wlr_deco = data; */

    wlr_log(WLR_DEBUG, "New server decoration");
}

static void handle_new_xdg_decoration(struct wl_listener* listener, void* data){
    /* struct wm_server* server = wl_container_of(listener, server, new_xdg_decoration); */
    /* struct wlr_xdg_toplevel_decoration_v1* wlr_deco = data; */

    wlr_log(WLR_DEBUG, "New XDG toplevel decoration");
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

    server->wlr_server_decoration_manager = wlr_server_decoration_manager_create(server->wl_display);
	wlr_server_decoration_manager_set_default_mode(server->wlr_server_decoration_manager, WLR_SERVER_DECORATION_MANAGER_MODE_SERVER);

    server->wlr_xdg_decoration_manager = wlr_xdg_decoration_manager_v1_create(server->wl_display);
    assert(server->wlr_xdg_decoration_manager);

    server->wlr_xwayland = 0;
#ifdef PYWM_XWAYLAND
    server->wlr_xwayland = wlr_xwayland_create(server->wl_display, server->wlr_compositor, false);
    assert(server->wlr_xwayland);

    server->wlr_xcursor_manager = wlr_xcursor_manager_create(NULL, 24);
    assert(server->wlr_xcursor_manager);

    if(wlr_xcursor_manager_load(server->wlr_xcursor_manager, 1)){
        wlr_log(WLR_ERROR, "Cannot load XCursor");
    }

    struct wlr_xcursor* xcursor = wlr_xcursor_manager_get_xcursor(server->wlr_xcursor_manager, "left_ptr", 1);
    if(xcursor){
        struct wlr_xcursor_image* image = xcursor->images[0];
        wlr_xwayland_set_cursor(server->wlr_xwayland,
                image->buffer, image->width * 4, image->width, image->height, image->hotspot_x, image->hotspot_y);
    }
#endif

    /* Children */
    server->wm_layout = calloc(1, sizeof(struct wm_layout));
    wm_layout_init(server->wm_layout, server);

    server->wm_seat = calloc(1, sizeof(struct wm_seat));
    wm_seat_init(server->wm_seat, server, server->wm_layout);

#ifdef PYWM_XWAYLAND
    wlr_xwayland_set_seat(server->wlr_xwayland, server->wm_seat->wlr_seat);
#endif

    /* Handlers */
    server->new_input.notify = handle_new_input;
    wl_signal_add(&server->wlr_backend->events.new_input, &server->new_input);

    server->new_output.notify = handle_new_output;
    wl_signal_add(&server->wlr_backend->events.new_output, &server->new_output);

    server->new_xdg_surface.notify = handle_new_xdg_surface;
    wl_signal_add(&server->wlr_xdg_shell->events.new_surface, &server->new_xdg_surface);

	server->new_server_decoration.notify = handle_new_server_decoration;
	wl_signal_add(&server->wlr_server_decoration_manager->events.new_decoration, &server->new_server_decoration);

    server->new_xdg_decoration.notify = handle_new_xdg_decoration;
    wl_signal_add(&server->wlr_xdg_decoration_manager->events.new_toplevel_decoration, &server->new_xdg_decoration);

#ifdef PYWM_XWAYLAND
    server->new_xwayland_surface.notify = handle_new_xwayland_surface;
    wl_signal_add(&server->wlr_xwayland->events.new_surface, &server->new_xwayland_surface);
#endif
}

void wm_server_destroy(struct wm_server* server){
#ifdef PYWM_XWAYLAND
    wlr_xwayland_destroy(server->wlr_xwayland);
#endif
    wl_display_destroy_clients(server->wl_display);
    wl_display_destroy(server->wl_display);

}

void wm_server_surface_at(struct wm_server* server, double at_x, double at_y, 
        struct wlr_surface** result, double* result_sx, double* result_sy){
    struct wm_view* view;
    wl_list_for_each(view, &server->wm_views, link){
        if(!view->mapped) continue;

        int width;
        int height;
        wm_view_get_size(view, &width, &height);

        double scale_x = view->display_width/width;
        double scale_y = view->display_height/height;

        int view_at_x = round((at_x - view->display_x) / scale_x);
        int view_at_y = round((at_y - view->display_y) / scale_y);

        double sx;
        double sy;
        struct wlr_surface* surface = wm_view_surface_at(view, view_at_x, view_at_y, &sx, &sy);

        if(surface){
            *result = surface;
            *result_sx = sx;
            *result_sy = sy;
            return;
        }
    }

    *result = NULL;
}

struct _view_for_surface_data {
    struct wlr_surface* surface;
    bool result;
};

static void _view_for_surface(struct wlr_surface* surface, int sx, int sy, void* _data){
    struct _view_for_surface_data* data = _data;
    if(surface == data->surface){
        data->result = true;
        return;
    }
}

struct wm_view* wm_server_view_for_surface(struct wm_server* server, struct wlr_surface* surface){
    struct wm_view* view;
    wl_list_for_each(view, &server->wm_views, link){
        struct _view_for_surface_data data = { 0 };
        data.surface = surface;
        wm_view_for_each_surface(view, _view_for_surface, &data);
        if(data.result){
            return view;
        }
    }

    return NULL;
}
