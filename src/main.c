#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <stdlib.h>
#include <unistd.h>

#include "wm/wm_config.h"
#include "wm/wm.h"


int main(int argc, char** argv){
    struct wm_config config;
    wm_config_init_default(&config);
    wm_init();
    wm_run();
    wm_destroy();

    return 0;
}
