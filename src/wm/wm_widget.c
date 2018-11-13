#include "wm/wm_widget.h"
#include "wm/wm_server.h"

void wm_widget_init(struct wm_widget* widget, struct wm_server* server){
    widget->wm_server = server;

    widget->layer = WM_WIDGET_BACK;
    widget->wlr_texture = NULL;
}

void wm_widget_destroy(struct wm_widget* widget){
    wl_list_remove(&widget->link);
    wlr_texture_destroy(widget->wlr_texture);
}

void wm_widget_set_pixels(struct wm_widget* widget, enum wl_shm_format format, uint32_t stride, uint32_t width, uint32_t height, const void* data){
    if(widget->wlr_texture){
        wlr_texture_write_pixels(widget->wlr_texture, stride, width, height, 0, 0, 0, 0, data);
    }else{
        widget->wlr_texture = wlr_texture_from_pixels(widget->wm_server->wlr_renderer, format, stride, width, height, data);
    }
}
void wm_widget_set_box(struct wm_widget* widget, double x, double y, double width, double height){
    widget->display_x = x;
    widget->display_y = y;
    widget->display_width = width;
    widget->display_height = height;
}
