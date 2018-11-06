#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <stdlib.h>
#include <unistd.h>

#include "wm.h"


int main(int argc, char** argv){
    struct wm wm;
    wm_init(&wm);
    int status = wm_run(&wm);
    wm_destroy(&wm);

    return status;
}
