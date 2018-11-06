#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
#include <wayland-server.h>
#include <wlr/backend.h>
#include <wlr/backend/headless.h>
#include <wlr/backend/multi.h>
#include <wlr/config.h>
#include <wlr/render/wlr_renderer.h>
#include <wlr/util/log.h>

#include "wm_server.h"

struct wm_server server = { 0 };

int main(int argc, char** argv){
    wlr_log_init(WLR_DEBUG, NULL);

    wm_server_init(&server);

    /* Setup socket and set env */
	const char *socket = wl_display_add_socket_auto(server.wl_display);
	if (!socket) {
		wlr_log_errno(WLR_ERROR, "Unable to open wayland socket");
		wlr_backend_destroy(server.wlr_backend);
		return 1;
	}

	wlr_log(WLR_INFO, "Running compositor on wayland display '%s'", socket);
	setenv("_WAYLAND_DISPLAY", socket, true);

	if (!wlr_backend_start(server.wlr_backend)) {
		wlr_log(WLR_ERROR, "Failed to start backend");
		wlr_backend_destroy(server.wlr_backend);
		wl_display_destroy(server.wl_display);
		return 1;
	}

	setenv("WAYLAND_DISPLAY", socket, true);

    /* Main */
    wl_display_run(server.wl_display);
    
    /* Cleanup */
    wm_server_destroy(&server);

    return 0;
}
