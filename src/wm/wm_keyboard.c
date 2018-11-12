#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <wayland-server.h>
#include <wlr/util/log.h>
#include <xkbcommon/xkbcommon.h>
#include "wm/wm_keyboard.h"
#include "wm/wm_seat.h"
#include "wm/wm.h"


#define KEYS_STRING_LENGTH 256

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

    xkb_keycode_t keycode = event->keycode + 8;
    size_t keysyms_len;
    const xkb_keysym_t* keysyms;

    keysyms_len = xkb_state_key_get_syms(keyboard->wlr_input_device->keyboard->xkb_state, keycode, &keysyms);

    char keys[KEYS_STRING_LENGTH] = { 0 };
    size_t at=0;
    for(size_t i=0; i<keysyms_len; i++){
        at += xkb_keysym_get_name(keysyms[i], keys + at, KEYS_STRING_LENGTH - at);
    }
    assert(at < KEYS_STRING_LENGTH - 1);

    if(wm_callback_key(event, keys)){
        return;
    }

    wm_seat_dispatch_key(keyboard->wm_seat, keyboard->wlr_input_device, event);
}

static void handle_modifiers(struct wl_listener* listener, void* data){
    struct wm_keyboard* keyboard = wl_container_of(listener, keyboard, modifiers);

    if(wm_callback_modifiers(&keyboard->wlr_input_device->keyboard->modifiers)){
        return;
    }

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
