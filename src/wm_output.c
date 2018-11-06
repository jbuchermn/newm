#define _POSIX_C_SOURCE 199309L

#include <time.h>
#include <wlr/util/log.h>
#include "wm_output.h"

/*
 * Callbacks
 */
static void handle_destroy(struct wl_listener* listener, void* data){
    struct wm_output* output = wl_container_of(listener, output, destroy);
    wm_output_destroy(output);
}

static void handle_mode(struct wl_listener* listener, void* data){
    struct wm_output* output = wl_container_of(listener, output, mode);
    wlr_log(WLR_DEBUG, "Mode event");
}

static void handle_transform(struct wl_listener* listener, void* data){
    struct wm_output* output = wl_container_of(listener, output, transform);
    wlr_log(WLR_DEBUG, "Transform event");
}

static void handle_present(struct wl_listener* listener, void* data){
    struct wm_output* output = wl_container_of(listener, output, present);
    wlr_log(WLR_DEBUG, "Present event");
}

static void handle_frame(struct wl_listener* listener, void* data){
    struct wm_output* output = wl_container_of(listener, output, frame);

	struct timespec now;
	clock_gettime(CLOCK_MONOTONIC, &now);

	if(!wlr_output_make_current(output->wlr_output, NULL)) {
		return;
	}

	int width, height;
	wlr_output_effective_resolution(output->wlr_output, &width, &height);
	wlr_renderer_begin(output->wlr_renderer, width, height);

	float color[4] = { 0.3, 0.3, 0.3, 1.0 };
	wlr_renderer_clear(output->wlr_renderer, color);

	wlr_renderer_end(output->wlr_renderer);
	wlr_output_swap_buffers(output->wlr_output, NULL, NULL);
}

/*
 * Class implementation
 */
void wm_output_init(struct wm_output* output, struct wm_layout* layout, struct wlr_output* out, struct wlr_renderer* renderer){
    output->wm_layout = layout;
    output->wlr_output = out;
    output->wlr_renderer = renderer;

    output->destroy.notify = handle_destroy;
    wl_signal_add(&output->wlr_output->events.destroy, &output->destroy);

    output->mode.notify = handle_mode;
    wl_signal_add(&output->wlr_output->events.mode, &output->mode);

    output->transform.notify = handle_transform;
    wl_signal_add(&output->wlr_output->events.transform, &output->transform);

    output->present.notify = handle_present;
    wl_signal_add(&output->wlr_output->events.present, &output->present);

    output->frame.notify = handle_frame;
    wl_signal_add(&output->wlr_output->events.frame, &output->frame);
}

void wm_output_destroy(struct wm_output* output){
    wl_list_remove(&output->destroy.link);
    wl_list_remove(&output->mode.link);
    wl_list_remove(&output->transform.link);
    wl_list_remove(&output->present.link);
    wl_list_remove(&output->link);
}
