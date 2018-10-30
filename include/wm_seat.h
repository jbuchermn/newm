#ifndef WM_SEAT_H
#define WM_SEAT_H

#include <wayland-server.h>
#include <wlr/types/wlr_input_device.h>
#include <wlr/types/wlr_seat.h>
#include "wm_server.h"
#include "wm_cursor.h"

struct wm_seat{
    struct wm_server* wm_server;

    struct wm_cursor* wm_cursor;

    struct wlr_seat* wlr_seat;
    struct wl_list wm_keyboards;
    struct wl_list wm_pointers;

    struct wl_listener destroy;
};

void wm_seat_init(struct wm_seat* seat, struct wm_server* server);
void wm_seat_destroy(struct wm_seat* seat);

void wm_seat_add_input_device(struct wm_seat* seat, struct wlr_input_device* input_device);

#endif
