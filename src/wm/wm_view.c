#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <stdlib.h>
#include <wayland-server.h>
#include <wlr/types/wlr_xdg_shell.h>
#include <wlr/util/log.h>
#include <wlr/xwayland.h>

#include "wm/wm_view.h"
#include "wm/wm_seat.h"
#include "wm/wm_server.h"
#include "wm/wm.h"

/*
 * Callbacks: xdg_toplevel_decoration
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

/*
 * Callbacks: xdg_surface
 */
static void handle_xdg_map(struct wl_listener* listener, void* data){
    struct wm_view* view = wl_container_of(listener, view, map);
    view->mapped = true;
}

static void handle_xdg_unmap(struct wl_listener* listener, void* data){
    struct wm_view* view = wl_container_of(listener, view, unmap);
    view->mapped = false;
    wm_callback_destroy_view(view);
}

static void handle_xdg_destroy(struct wl_listener* listener, void* data){
    struct wm_view* view = wl_container_of(listener, view, destroy);
    wm_view_destroy(view);
    free(view);
}


/*
 * Callbacks: xwayland_surface
 */
static void handle_xwayland_map(struct wl_listener* listener, void* data){
    struct wm_view* view = wl_container_of(listener, view, map);
    view->mapped = true;
}

static void handle_xwayland_unmap(struct wl_listener* listener, void* data){
    struct wm_view* view = wl_container_of(listener, view, unmap);
    view->mapped = false;
    wm_callback_destroy_view(view);
}

static void handle_xwayland_destroy(struct wl_listener* listener, void* data){
    struct wm_view* view = wl_container_of(listener, view, destroy);
    wm_view_destroy(view);
    free(view);
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

void wm_view_init_xdg(struct wm_view* view, struct wm_server* server, struct wlr_xdg_surface* surface){
    view->kind = WM_VIEW_XDG;

    view->wm_server = server;
    view->wlr_xdg_surface = surface;
    view->title = surface->toplevel->title;
    view->app_id = surface->toplevel->app_id;

    wlr_log(WLR_DEBUG, "New wm_view (xdg): %s, %s", view->title, view->app_id);

    view->mapped = false;

    view->map.notify = &handle_xdg_map;
    wl_signal_add(&surface->events.map, &view->map);

    view->unmap.notify = &handle_xdg_unmap;
    wl_signal_add(&surface->events.unmap, &view->unmap);

    view->destroy.notify = &handle_xdg_destroy;
    wl_signal_add(&surface->events.destroy, &view->destroy);

    wm_callback_init_view(view);

    /* Get rid of white spaces around; therefore geometry.width/height should always equal current.width/height */
    wlr_xdg_toplevel_set_tiled(surface, 15);
}

void wm_view_init_xwayland(struct wm_view* view, struct wm_server* server, struct wlr_xwayland_surface* surface){
    view->kind = WM_VIEW_XWAYLAND;

    view->wm_server = server;
    view->wlr_xwayland_surface = surface;
    view->title = surface->title;
    view->app_id = surface->instance;

    wlr_log(WLR_DEBUG, "New wm_view (xwayland): %s, %s", view->title, view->app_id);

    view->mapped = false;

    view->map.notify = &handle_xwayland_map;
    wl_signal_add(&surface->events.map, &view->map);

    view->unmap.notify = &handle_xwayland_unmap;
    wl_signal_add(&surface->events.unmap, &view->unmap);

    view->destroy.notify = &handle_xwayland_destroy;
    wl_signal_add(&surface->events.destroy, &view->destroy);

    wm_callback_init_view(view);

}

void wm_view_destroy(struct wm_view* view){
    wl_list_remove(&view->map.link);
    wl_list_remove(&view->unmap.link);
    wl_list_remove(&view->destroy.link);
    wl_list_remove(&view->link);
}

void wm_view_set_box(struct wm_view* view, double x, double y, double width, double height){
    wlr_log(WLR_DEBUG, "%f, %f, %f, %f\n", x, y, width, height);

    view->display_x = x;
    view->display_y = y;
    view->display_width = width;
    view->display_height = height;
}

void wm_view_request_size(struct wm_view* view, int width, int height){
    switch(view->kind){
    case WM_VIEW_XDG:
        if(!view->wlr_xdg_surface){
            wlr_log(WLR_DEBUG, "Warning: view with wlr_xdg_surface == 0");
            return;
        }

        if(view->wlr_xdg_surface->role == WLR_XDG_SURFACE_ROLE_TOPLEVEL){
            wlr_xdg_toplevel_set_size(view->wlr_xdg_surface, width, height);
        }else{
            wlr_log(WLR_DEBUG, "Warning: Can only set size on toplevel");
        }
        break;
    case WM_VIEW_XWAYLAND:
        wlr_xwayland_surface_configure(view->wlr_xwayland_surface, view->display_x, view->display_y, width, height);
        break;
    }
}

void wm_view_get_size(struct wm_view* view, int* width, int* height){
    switch(view->kind){
    case WM_VIEW_XDG:
        /* Fixed by set_tiled */
        /* Although during updates not strictly equal? */
        /* assert(view->wlr_xdg_surface->geometry.width == view->wlr_xdg_surface->surface->current.width); */
        /* assert(view->wlr_xdg_surface->geometry.height == view->wlr_xdg_surface->surface->current.height); */

        if(!view->wlr_xdg_surface){
            *width = 0;
            *height = 0;

            wlr_log(WLR_DEBUG, "Warning: view with wlr_xdg_surface == 0");
            return;
        }

        *width = view->wlr_xdg_surface->geometry.width;
        *height = view->wlr_xdg_surface->geometry.height;
        break;
    case WM_VIEW_XWAYLAND:
        if(!view->wlr_xwayland_surface->surface){
            *width = 0;
            *height = 0;

            wlr_log(WLR_DEBUG, "Warning: view with wlr_surface == 0");
            return;
        }

        *width = view->wlr_xwayland_surface->surface->current.width;
        *height = view->wlr_xwayland_surface->surface->current.height;
        break;
    }
}

void wm_view_focus(struct wm_view* view, struct wm_seat* seat){
    switch(view->kind){
    case WM_VIEW_XDG:
        wm_seat_focus_surface(seat, view->wlr_xdg_surface->surface);
        break;
    case WM_VIEW_XWAYLAND:
        if(!view->wlr_xwayland_surface->surface){
            wlr_log(WLR_DEBUG, "Warning: view with wlr_surface == 0");
            return;
        }
        wm_seat_focus_surface(seat, view->wlr_xwayland_surface->surface);
        break;
    }
}

struct wlr_surface* wm_view_surface_at(struct wm_view* view, double at_x, double at_y, double* sx, double* sy){
    switch(view->kind){
    case WM_VIEW_XDG:
        return wlr_xdg_surface_surface_at(view->wlr_xdg_surface, at_x, at_y, sx, sy);
    case WM_VIEW_XWAYLAND:
        if(!view->wlr_xwayland_surface->surface){
            wlr_log(WLR_DEBUG, "Warning: view with wlr_surface == 0");
            return NULL;
        }

        return wlr_surface_surface_at(view->wlr_xwayland_surface->surface, at_x, at_y, sx, sy);
    }
}

void wm_view_for_each_surface(struct wm_view* view, wlr_surface_iterator_func_t iterator, void* user_data){
    switch(view->kind){
    case WM_VIEW_XDG:
        wlr_xdg_surface_for_each_surface(view->wlr_xdg_surface, iterator, user_data);
        break;
    case WM_VIEW_XWAYLAND:
        wlr_surface_for_each_surface(view->wlr_xwayland_surface->surface, iterator, user_data);
        break;
    }
}
