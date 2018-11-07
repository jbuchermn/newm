#ifndef _PYWM_CALLBACKS_H
#define _PYWM_CALLBACKS_H

#include <Python.h>

struct _pywm_callbacks {
    PyObject* motion;
    PyObject* motion_absolute;
    PyObject* button;
    PyObject* axis;
    PyObject* key;
    PyObject* modifiers;

    PyObject* init_view;
    PyObject* destroy_view;
};

void _pywm_callbacks_init();
PyObject** _pywm_callbacks_get(const char* name);

#endif
