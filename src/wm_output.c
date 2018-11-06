#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <time.h>
#include <wlr/util/log.h>
#include <wlr/render/wlr_renderer.h>
#include <wlr/types/wlr_matrix.h>
#include "wm_server.h"
#include "wm_output.h"
#include "wm_view.h"
#include "wm_layout.h"

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
	struct wlr_renderer *renderer;
	struct wm_view *view;
	struct timespec when;
};

static void render_surface(struct wlr_surface *surface, int sx, int sy, void *data) {
	struct render_data *rdata = data;
	struct wm_view *view = rdata->view;
	struct wm_output *output = rdata->output;

	struct wlr_texture *texture = wlr_surface_get_texture(surface);
	if(!texture) {
		return;
	}

    wm_view_update(view, rdata->when);

	double ox = 0, oy = 0;
	wlr_output_layout_output_coords(output->wm_layout->wlr_output_layout, output->wlr_output, &ox, &oy);
	ox += view->x + sx;
    oy += view->y + sy;

	struct wlr_box box = {
		.x = ox * output->wlr_output->scale,
		.y = oy * output->wlr_output->scale,
		.width = view->scale * surface->current.width * output->wlr_output->scale,
		.height = view->scale * surface->current.height * output->wlr_output->scale,
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
		if (!view->mapped) {
			continue;
		}

		struct render_data rdata = {
			.output = output,
			.view = view,
			.when = now,
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
