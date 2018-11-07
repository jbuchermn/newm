#define _POSIX_C_SOURCE 200112L

#include <stdlib.h>
#include <assert.h>
#include <wlr/util/log.h>
#include "wm_layout.h"
#include "wm_output.h"
#include "wm.h"

/*
 * Callbacks
 */
static void handle_change(struct wl_listener* listener, void* data){
    struct wm_layout* layout = wl_container_of(listener, layout, change);

    wm_callback_layout_change(layout);
}

/*
 * Class implementation
 */
void wm_layout_init(struct wm_layout* layout, struct wm_server* server){
    layout->wm_server = server;
    wl_list_init(&layout->wm_outputs);

    layout->wlr_output_layout = wlr_output_layout_create();
    assert(layout->wlr_output_layout);

    layout->change.notify = &handle_change;
    wl_signal_add(&layout->wlr_output_layout->events.change, &layout->change);
}

void wm_layout_destroy(struct wm_layout* layout) {
    wl_list_remove(&layout->change.link);
}

void wm_layout_add_output(struct wm_layout* layout, struct wlr_output* out){
    wlr_log(WLR_DEBUG, "New output: %s", out->name);

    struct wm_output* output = calloc(1, sizeof(struct wm_output));
    wm_output_init(output, layout->wm_server, layout, out);
    wl_list_insert(&layout->wm_outputs, &output->link);

    wlr_output_layout_add_auto(layout->wlr_output_layout, out);
}
