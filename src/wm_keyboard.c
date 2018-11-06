#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <wayland-server.h>
#include <wlr/util/log.h>
#include <xkbcommon/xkbcommon.h>
#include "wm_keyboard.h"
#include "wm_seat.h"

/*
 * Callbacks
 */
static void handle_destroy(struct wl_listener* listener, void* data){
    struct wm_keyboard* keyboard = wl_container_of(listener, keyboard, destroy);
    wm_keyboard_destroy(keyboard);
}

static void handle_key(struct wl_listener* listener, void* data){
    struct wm_keyboard* keyboard = wl_container_of(listener, keyboard, key);
    struct wlr_event_keyboard_key* event = data;

    /* Custom input handling here */

    wm_seat_dispatch_key(keyboard->wm_seat, keyboard->wlr_input_device, event);
}

static void handle_modifiers(struct wl_listener* listener, void* data){
    struct wm_keyboard* keyboard = wl_container_of(listener, keyboard, modifiers);

    /* Custom input handling here */

    wm_seat_dispatch_modifiers(keyboard->wm_seat, keyboard->wlr_input_device);
}

/*
 * Class implementation
 */
void wm_keyboard_init(struct wm_keyboard* keyboard, struct wm_seat* seat, struct wlr_input_device* input_device){
    keyboard->wm_seat = seat;
    keyboard->wlr_input_device = input_device;
    input_device->data = keyboard;

    /* Configuration */
	struct xkb_rule_names rules = { 0 };
	rules.layout = "de,de";
	struct xkb_context* context = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
    assert(context);
	struct xkb_keymap* keymap = xkb_map_new_from_names(context, &rules, XKB_KEYMAP_COMPILE_NO_FLAGS);
    assert(keymap);

	wlr_keyboard_set_keymap(keyboard->wlr_input_device->keyboard, keymap);
	wlr_keyboard_set_repeat_info(keyboard->wlr_input_device->keyboard, 25, 600);

	xkb_keymap_unref(keymap);
	xkb_context_unref(context);

    /* Handlers */
    keyboard->destroy.notify = handle_destroy;
    wl_signal_add(&keyboard->wlr_input_device->events.destroy, &keyboard->destroy);

    keyboard->key.notify = handle_key;
    wl_signal_add(&keyboard->wlr_input_device->keyboard->events.key, &keyboard->key);

    keyboard->modifiers.notify = handle_modifiers;
    wl_signal_add(&keyboard->wlr_input_device->keyboard->events.modifiers, &keyboard->modifiers);
}

void wm_keyboard_destroy(struct wm_keyboard* keyboard){
    wl_list_remove(&keyboard->destroy.link);
    wl_list_remove(&keyboard->key.link);
    wl_list_remove(&keyboard->modifiers.link);
    wl_list_remove(&keyboard->link);
}
