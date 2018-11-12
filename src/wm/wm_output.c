#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <time.h>
#include <wlr/util/log.h>
#include <wlr/render/wlr_renderer.h>
#include <wlr/types/wlr_matrix.h>
#include "wm/wm_server.h"
#include "wm/wm_output.h"
#include "wm/wm_view.h"
#include "wm/wm_layout.h"

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
}

struct render_data {
	struct wm_output *output;
	struct timespec when;
    double x;
    double y;
    double x_scale;
    double y_scale;
};

static void render_surface(struct wlr_surface *surface, int sx, int sy, void *data) {
	struct render_data *rdata = data;
	struct wm_output *output = rdata->output;

	struct wlr_texture *texture = wlr_surface_get_texture(surface);
	if(!texture) {
		return;
	}

	/* 
     * TODO!
     * * wlr_output_layout_output_coords: Placement of output within layout
     */
	struct wlr_box box = {
		.x = round((rdata->x + sx*rdata->x_scale) * output->wlr_output->scale),
		.y = round((rdata->y + sy*rdata->y_scale) * output->wlr_output->scale),
		.width = round(surface->current.width * rdata->x_scale * output->wlr_output->scale),
		.height = round(surface->current.height * rdata->y_scale * output->wlr_output->scale)
	};

	float matrix[9];
	enum wl_output_transform transform = wlr_output_transform_invert(surface->current.transform);
	wlr_matrix_project_box(matrix, &box, transform, 0, output->wlr_output->transform_matrix);

    /* Actual rendering */
	wlr_render_texture_with_matrix(output->wm_server->wlr_renderer, texture, matrix, 1);

    /* Notify client */
	wlr_surface_send_frame_done(surface, &rdata->when);
}

static void handle_frame(struct wl_listener* listener, void* data){
    struct wm_output* output = wl_container_of(listener, output, frame);
    struct wlr_renderer* wlr_renderer = output->wm_server->wlr_renderer;

	struct timespec now;
	clock_gettime(CLOCK_MONOTONIC, &now);

	if(!wlr_output_make_current(output->wlr_output, NULL)) {
		return;
	}

	int width, height;
	wlr_output_effective_resolution(output->wlr_output, &width, &height);
	wlr_renderer_begin(wlr_renderer, width, height);

	float color[4] = { 0.3, 0.3, 0.3, 1.0 };
	wlr_renderer_clear(wlr_renderer, color);

	struct wm_view *view;
	wl_list_for_each_reverse(view, &output->wm_server->wm_views, link) {
        if(!view->mapped){
            continue;
        }

        int width, height;
        wm_view_get_size(view, &width, &height);

		struct render_data rdata = {
			.output = output,
			.when = now,
            .x = view->display_x,
            .y = view->display_y,
            .x_scale = view->display_width / width,
            .y_scale = view->display_height / height
		};

		wlr_xdg_surface_for_each_surface(view->wlr_xdg_surface,
				render_surface, &rdata);
	}

	wlr_renderer_end(wlr_renderer);
	wlr_output_swap_buffers(output->wlr_output, NULL, NULL);
}

/*
 * Class implementation
 */
void wm_output_init(struct wm_output* output, struct wm_server* server, struct wm_layout* layout, struct wlr_output* out){
    output->wm_server = server;
    output->wm_layout = layout;
    output->wlr_output = out;

    /* Set mode */
    if(!wl_list_empty(&output->wlr_output->modes)){
        struct wlr_output_mode* mode = wl_container_of(output->wlr_output->modes.prev, mode, link);
        wlr_output_set_mode(output->wlr_output, mode);
    }

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
