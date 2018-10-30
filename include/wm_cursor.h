#ifndef WM_CURSOR_H
#define WM_CURSOR_H

#include <wayland-server.h>
#include <wlr/types/wlr_cursor.h>
#include "wm_seat.h"
#include "wm_pointer.h"

struct wm_cursor {
    struct wm_seat* wm_seat;

    struct wlr_cursor* wlr_cursor;

    struct wl_listener motion;
    struct wl_listener motion_absolute;
    struct wl_listener button;
    struct wl_listener axis;
};

void wm_cursor_init(struct wm_cursor* cursor, struct wm_seat* seat);
void wm_cursor_destroy(struct wm_cursor* cursor);
void wm_cursor_add_pointer(struct wm_cursor* cursor, struct wm_pointer* pointer);


#endif
