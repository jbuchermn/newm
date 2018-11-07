#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <wlr/util/log.h>
#include "wm_cursor.h"
#include "wm_seat.h"
#include "wm_layout.h"
#include "wm_pointer.h"
#include "wm.h"

/*
 * Callbacks
 */
static void handle_motion(struct wl_listener* listener, void* data){
    struct wm_cursor* cursor = wl_container_of(listener, cursor, motion);
    struct wlr_event_pointer_motion* event = data;

    if(wm_callback_motion(event->delta_x, event->delta_y, event->time_msec)){
        return;
    }

    wlr_cursor_move(cursor->wlr_cursor, event->device, event->delta_x, event->delta_y);
    if(!wm_seat_dispatch_motion(cursor->wm_seat, cursor->wlr_cursor->x, cursor->wlr_cursor->y, event->time_msec)){
        wlr_xcursor_manager_set_cursor_image(cursor->wlr_xcursor_manager, "left_ptr", cursor->wlr_cursor);
    }
}

static void handle_motion_absolute(struct wl_listener* listener, void* data){
    struct wm_cursor* cursor = wl_container_of(listener, cursor, motion_absolute);
    struct wlr_event_pointer_motion_absolute* event = data;

    if(wm_callback_motion_absolute(event->x, event->y, event->time_msec)){
        return;
    }

    wlr_cursor_warp_absolute(cursor->wlr_cursor, event->device, event->x, event->y);
    if(!wm_seat_dispatch_motion(cursor->wm_seat, cursor->wlr_cursor->x, cursor->wlr_cursor->y, event->time_msec)){
        wlr_xcursor_manager_set_cursor_image(cursor->wlr_xcursor_manager, "left_ptr", cursor->wlr_cursor);
    }
}

static void handle_button(struct wl_listener* listener, void* data){
    struct wm_cursor* cursor = wl_container_of(listener, cursor, button);
    struct wlr_event_pointer_button* event = data;

    if(wm_callback_button(event)){
        return;
    }

    wm_seat_dispatch_button(cursor->wm_seat, event);
}

static void handle_axis(struct wl_listener* listener, void* data){
    struct wm_cursor* cursor = wl_container_of(listener, cursor, axis);
    struct wlr_event_pointer_axis* event = data;

    if(wm_callback_axis(event)){
        return;
    }

    wm_seat_dispatch_axis(cursor->wm_seat, event);
}

/*
 * Class implementation
 */
void wm_cursor_init(struct wm_cursor* cursor, struct wm_seat* seat, struct wm_layout* layout){
    cursor->wm_seat = seat;

    cursor->wlr_cursor = wlr_cursor_create();
    assert(cursor->wlr_cursor);

    wlr_cursor_attach_output_layout(cursor->wlr_cursor, layout->wlr_output_layout);

    cursor->wlr_xcursor_manager = wlr_xcursor_manager_create(NULL, 24);
    wlr_xcursor_manager_load(cursor->wlr_xcursor_manager, 1);

    cursor->motion.notify = handle_motion;
    wl_signal_add(&cursor->wlr_cursor->events.motion, &cursor->motion);

    cursor->motion_absolute.notify = handle_motion_absolute;
    wl_signal_add(&cursor->wlr_cursor->events.motion_absolute, &cursor->motion_absolute);

    cursor->button.notify = handle_button;
    wl_signal_add(&cursor->wlr_cursor->events.button, &cursor->button);

    cursor->axis.notify = handle_axis;
    wl_signal_add(&cursor->wlr_cursor->events.axis, &cursor->axis);

}

void wm_cursor_destroy(struct wm_cursor* cursor) {
    wl_list_remove(&cursor->motion.link);
    wl_list_remove(&cursor->motion_absolute.link);
    wl_list_remove(&cursor->button.link);
    wl_list_remove(&cursor->axis.link);
}

void wm_cursor_add_pointer(struct wm_cursor* cursor, struct wm_pointer* pointer){
    wlr_cursor_attach_input_device(cursor->wlr_cursor, pointer->wlr_input_device);
}
