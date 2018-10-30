#ifndef WM_LAYOUT_H
#define WM_LAYOUT_H

#include <wayland-server.h>
#include <wlr/types/wlr_output.h>
#include <wlr/types/wlr_output_layout.h>
#include "wm_server.h"

struct wm_layout {
    struct wm_server* wm_server;

    struct wlr_output_layout* wlr_output_layout;
    struct wl_list wm_outputs; // wm_output::link
};

void wm_layout_init(struct wm_layout* layout, struct wm_server* server);
void wm_layout_destroy(struct wm_layout* layout);

void wm_layout_add_output(struct wm_layout* layout, struct wlr_output* output);

#endif
