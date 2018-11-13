#ifndef WM_WIDGET_H
#define WM_WIDGET_H

#include <stdbool.h>
#include <wayland-server.h>
#include <wlr/render/wlr_texture.h>

struct wm_server;

struct wm_widget {
    struct wl_list link;  // wm_server::wm_widgets
    struct wm_server* wm_server;

    struct wlr_texture* wlr_texture;

    double display_x;
    double display_y;
    double display_width;
    double display_height;

    enum {
        WM_WIDGET_BACK,
        WM_WIDGET_FRONT
    } layer;
};

void wm_widget_init(struct wm_widget* widget, struct wm_server* server);
void wm_widget_destroy(struct wm_widget* widget);

void wm_widget_set_pixels(struct wm_widget* widget, enum wl_shm_format format, uint32_t stride, uint32_t width, uint32_t height, const void* data);
void wm_widget_set_box(struct wm_widget* widget, double x, double y, double width, double height);

#endif
