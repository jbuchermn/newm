#define _POSIX_C_SOURCE 200112L

#include <wayland-server.h>
#include <wlr/util/log.h>
#include "wm/wm_pointer.h"
#include "wm/wm_seat.h"

/*
 * Callbacks
 */
static void handle_destroy(struct wl_listener* listener, void* data){
    struct wm_pointer* pointer = wl_container_of(listener, pointer, destroy);
    wm_pointer_destroy(pointer);
}

/*
 * Class implementation
 */
void wm_pointer_init(struct wm_pointer* pointer, struct wm_seat* seat, struct wlr_input_device* input_device){
    pointer->wm_seat = seat;
    pointer->wlr_input_device = input_device;
    input_device->data = pointer;

    pointer->destroy.notify = handle_destroy;
    wl_signal_add(&pointer->wlr_input_device->events.destroy, &pointer->destroy);
}

void wm_pointer_destroy(struct wm_pointer* pointer){
    wl_list_remove(&pointer->link);
}
