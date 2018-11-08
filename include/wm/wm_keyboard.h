#ifndef WM_KEYBOARD_H
#define WM_KEYBOARD_H

#include <wayland-server.h>
#include <wlr/types/wlr_input_device.h>

struct wm_seat;

struct wm_keyboard {
    struct wl_list link;   // wm_seat::wm_keyboards
    struct wm_seat* wm_seat;

    struct wlr_input_device* wlr_input_device;

    struct wl_listener destroy;
    struct wl_listener key;
    struct wl_listener modifiers;
};

void wm_keyboard_init(struct wm_keyboard* keyboard, struct wm_seat* seat, struct wlr_input_device* input_device);
void wm_keyboard_destroy(struct wm_keyboard* keyboard);


#endif
