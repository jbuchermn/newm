#ifndef WM_CONFIG_H
#define WM_CONFIG_H

struct wm_config {
    double output_scale;
    const char* xcursor_theme;
    const char* xcursor_name;
    int xcursor_size;
};

void wm_config_init_default(struct wm_config* config);

#endif
