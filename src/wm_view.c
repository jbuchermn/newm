#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <stdlib.h>
#include <wayland-server.h>
#include <wlr/types/wlr_xdg_shell.h>
#include <wlr/util/log.h>

#include "wm_view.h"

/*
 * Callbacks
 */
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



/*
 * Class implementation
 */
void wm_view_init(struct wm_view* view, struct wlr_xdg_surface* surface){
    view->wlr_xdg_surface = surface;
    view->mapped = false;
    view->x = 20;
    view->y = 20;

    wlr_log(WLR_DEBUG, "New view");

    view->map.notify = &handle_map;
    wl_signal_add(&surface->events.map, &view->map);
    view->unmap.notify = &handle_unmap;
    wl_signal_add(&surface->events.unmap, &view->map);
    view->destroy.notify = &handle_destroy;
    wl_signal_add(&surface->events.destroy, &view->map);
}

void wm_view_destroy(struct wm_view* view){
    wl_list_remove(&view->link);
}
