#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <stdlib.h>
#include <unistd.h>

#include "wm/wm.h"


int main(int argc, char** argv){
    wm_init();
    wm_run();
    wm_join();
    wm_destroy();

    return 0;
}
