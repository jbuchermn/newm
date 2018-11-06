#ifndef WM_H
#define WM_H

#include <pthread.h>

struct wm_server;

struct wm {
    pthread_t thread;
    struct wm_server* server;
};

void wm_init();
void wm_destroy();
int wm_run();
void wm_terminate();

#endif
