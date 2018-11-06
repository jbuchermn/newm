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

static void handle_commit(struct wl_listener* listener, void* data){
    struct wm_view* view = wl_container_of(listener, view, commit);
}


/*
 * Class implementation
 */
void wm_view_init(struct wm_view* view, struct wm_server* server, struct wlr_xdg_surface* surface){
    view->wm_server = server;
    view->wlr_xdg_surface = surface;
    view->mapped = false;
    static int x = 0;
    view->x = x;
    view->y = 0;
    view->scale = 1.;

    view->width = 400;
    view->height = 400;

    x+=400;


    view->map.notify = &handle_map;
    wl_signal_add(&surface->events.map, &view->map);

    view->unmap.notify = &handle_unmap;
    wl_signal_add(&surface->events.unmap, &view->unmap);

    view->destroy.notify = &handle_destroy;
    wl_signal_add(&surface->events.destroy, &view->destroy);

    view->commit.notify = &handle_commit;
    wl_signal_add(&surface->surface_commit, &view->commit);
}

void wm_view_destroy(struct wm_view* view){
    wl_list_remove(&view->link);
}

void wm_view_update(struct wm_view* view, struct timespec when){

    static int counter = 0;
    counter++;

    if(counter % 10 == 0){
        view->width*=1.01;
        view->height*=1.01;
        view->scale=400./view->width;

    }
    
    /* Custom handling of x, y, width, height, scale */

    if(view->wlr_xdg_surface->surface->current.width != view->width &&
            view->wlr_xdg_surface->surface->current.height != view->height){
        wlr_xdg_toplevel_set_size(view->wlr_xdg_surface, view->width, view->height);
    }
}
