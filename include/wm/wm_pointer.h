#ifndef WM_POINTER_H
#define WM_POINTER_H

#include <wayland-server.h>
#include <wlr/types/wlr_input_device.h>

struct wm_seat;

struct wm_pointer {
    struct wl_list link;   // wm_seat::wm_pointers
    struct wm_seat* wm_seat;

    struct wlr_input_device* wlr_input_device;

    struct wl_listener destroy;
};

void wm_pointer_init(struct wm_pointer* pointer, struct wm_seat* seat, struct wlr_input_device* input_device);
void wm_pointer_destroy(struct wm_pointer* pointer);


#endif
