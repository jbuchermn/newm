#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <stdlib.h>
#include <wayland-server.h>
#include <wlr/types/wlr_xdg_shell.h>
#include <wlr/util/log.h>

#include "wm_view.h"
#include "wm_server.h"

/*
 * Callbacks
 */
static void handle_deco_request_mode(struct wl_listener* listener, void* data){
    struct wm_view_decoration* deco = wl_container_of(listener, deco, request_mode);
    
    wlr_xdg_toplevel_decoration_v1_set_mode(deco->wlr_xdg_toplevel_decoration,
        WLR_XDG_TOPLEVEL_DECORATION_V1_MODE_SERVER_SIDE);
}

static void handle_deco_destroy(struct wl_listener* listener, void* data){
    struct wm_view_decoration* deco = wl_container_of(listener, deco, destroy);
    wm_view_decoration_destroy(deco);
    free(deco);
}

static void handle_map(struct wl_listener* listener, void* data){
    struct wm_view* view = wl_container_of(listener, view, map);
    view->mapped = true;
}

static void handle_unmap(struct wl_listener* listener, void* data){
    struct wm_view* view = wl_container_of(listener, view, unmap);
    view->mapped = false;
}

static void handle_destroy(struct wl_listener* listener, void* data){
    struct wm_view* view = wl_container_of(listener, view, destroy);
    wm_view_destroy(view);
    free(view);
}

static void handle_new_popup(struct wl_listener* listener, void* data){
    struct wm_view* view = wl_container_of(listener, view, new_popup);

    /* TODO! */
}


/*
 * Class implementation
 */
void wm_view_decoration_init(struct wm_view_decoration* deco, struct wlr_xdg_toplevel_decoration_v1* wlr_deco){
    deco->wlr_xdg_toplevel_decoration = wlr_deco;

    deco->request_mode.notify = &handle_deco_request_mode;
    wl_signal_add(&wlr_deco->events.request_mode, &deco->request_mode);

    deco->destroy.notify = &handle_deco_destroy;
    wl_signal_add(&wlr_deco->events.destroy, &deco->destroy);
}

void wm_view_decoration_destroy(struct wm_view_decoration* deco){
    wl_list_remove(&deco->request_mode.link);
    wl_list_remove(&deco->destroy.link);
    wl_list_remove(&deco->link);
}

void wm_view_init(struct wm_view* view, struct wm_server* server, struct wlr_xdg_surface* surface){
    view->wm_server = server;
    view->wlr_xdg_surface = surface;
    view->mapped = false;
    view->x = 0;
    view->y = 0;
    view->scale = 1.;

    view->width = 1000;
    view->height = 1000;

    view->map.notify = &handle_map;
    wl_signal_add(&surface->events.map, &view->map);

    view->unmap.notify = &handle_unmap;
    wl_signal_add(&surface->events.unmap, &view->unmap);

    view->destroy.notify = &handle_destroy;
    wl_signal_add(&surface->events.destroy, &view->destroy);

    view->new_popup.notify = &handle_new_popup;
    wl_signal_add(&surface->events.new_popup, &view->new_popup);
}

void wm_view_destroy(struct wm_view* view){
    wl_list_remove(&view->map.link);
    wl_list_remove(&view->unmap.link);
    wl_list_remove(&view->destroy.link);
    wl_list_remove(&view->new_popup.link);
    wl_list_remove(&view->link);
}

void wm_view_update(struct wm_view* view, struct timespec when){
    
    /* Custom handling of x, y, width, height, scale */

    if(view->wlr_xdg_surface->surface->current.width != view->width &&
            view->wlr_xdg_surface->surface->current.height != view->height){
        wlr_xdg_toplevel_set_size(view->wlr_xdg_surface, view->width, view->height);
    }
}
