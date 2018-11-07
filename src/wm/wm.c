#define _POSIX_C_SOURCE 200112L

#include "wm.h"

#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
#include <wayland-server.h>
#include <wlr/backend.h>
#include <wlr/util/log.h>

#include "wm_server.h"
#include "wm_layout.h"
#include "wm_view.h"

struct wm wm = { 0 };

void wm_init(){
    if(!wm.server) wm.server = calloc(1, sizeof(struct wm_server));
}

void wm_destroy(){
    if(!wm.server) return;

    wm_server_destroy(wm.server);
    free(wm.server);
    wm.server = 0;
}

void* run(void* ignore){
    if(!wm.server) return NULL;

    wlr_log_init(WLR_DEBUG, NULL);

    wm_server_init(wm.server);

    /* Setup socket and set env */
	const char *socket = wl_display_add_socket_auto(wm.server->wl_display);
	if (!socket) {
		wlr_log_errno(WLR_ERROR, "Unable to open wayland socket");
		wlr_backend_destroy(wm.server->wlr_backend);
		return NULL;
	}

	wlr_log(WLR_INFO, "Running compositor on wayland display '%s'", socket);
	setenv("_WAYLAND_DISPLAY", socket, true);

	if (!wlr_backend_start(wm.server->wlr_backend)) {
		wlr_log(WLR_ERROR, "Failed to start backend");
		wlr_backend_destroy(wm.server->wlr_backend);
		wl_display_destroy(wm.server->wl_display);
		return NULL;
	}

	setenv("WAYLAND_DISPLAY", socket, true);

    /* Main */
    wl_display_run(wm.server->wl_display);

    return NULL;
}

int wm_run(){
    if(!wm.server) return 2;

    pthread_create(&wm.thread, NULL, &run, NULL);

    return 0;
}

void wm_join(){
    if(!wm.server) return;

    pthread_join(wm.thread, NULL);
}

void wm_terminate(){
    if(!wm.server) return;

    wl_display_terminate(wm.server->wl_display);
    wm_join();
}

struct wm* get_wm(){
    return &wm;
}

/*
 * Callbacks
 */
void wm_callback_layout_change(struct wm_layout* layout){
    if(!wm.callback_layout_change){
        return;
    }

    return (*wm.callback_layout_change)(layout);
}

bool wm_callback_key(struct wlr_event_keyboard_key* event){
    if(!wm.callback_key){
        return false;
    }

    return (*wm.callback_key)(event);
}

bool wm_callback_modifiers(struct wlr_keyboard_modifiers* modifiers){
    if(!wm.callback_modifiers){
        return false;
    }

    return (*wm.callback_modifiers)(modifiers);
}

bool wm_callback_motion(double delta_x, double delta_y, uint32_t time_msec){
    if(!wm.callback_motion){
        return false;
    }

    return (*wm.callback_motion)(delta_x, delta_y, time_msec);
}

bool wm_callback_motion_absolute(double x, double y, uint32_t time_msec){
    if(!wm.callback_motion_absolute){
        return false;
    }

    return (*wm.callback_motion_absolute)(x, y, time_msec);
}

bool wm_callback_button(struct wlr_event_pointer_button* event){
    if(!wm.callback_button){
        return false;
    }

    return (*wm.callback_button)(event);
}

bool wm_callback_axis(struct wlr_event_pointer_axis* event){
    if(!wm.callback_axis){
        return false;
    }

    return (*wm.callback_axis)(event);
}

void wm_callback_init_view(struct wm_view* view){
    if(!wm.callback_init_view){
        return;
    }

    return (*wm.callback_init_view)(view);
}

void wm_callback_update_view(struct wm_view* view, struct timespec when){
    if(!wm.callback_update_view){
        return;
    }

    return (*wm.callback_update_view)(view, when);
}

void wm_callback_destroy_view(struct wm_view* view){
    if(!wm.callback_destroy_view){
        return;
    }

    return (*wm.callback_destroy_view)(view);
}
