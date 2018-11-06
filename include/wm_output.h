#ifndef WM_OUTPUT_H
#define WM_OUTPUT_H

#include <wayland-server.h>
#include <wlr/types/wlr_output.h>
#include "wm_layout.h"

struct wm_output {
    struct wm_layout* wm_layout;
    struct wl_list link; // wm_layout::wm_outputs

    struct wlr_output* wlr_output;
    struct wlr_renderer* wlr_renderer;

    struct wl_listener destroy;
    struct wl_listener mode;
    struct wl_listener transform;
    struct wl_listener present;
    struct wl_listener frame;
};

void wm_output_init(struct wm_output* output, struct wm_layout* layout, struct wlr_output* out, struct wlr_renderer* renderer);
void wm_output_destroy(struct wm_output* output);


#endif
