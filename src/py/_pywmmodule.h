#ifndef _PYWMMODULE_H
#define _PYWMMODULE_H

#include <Python.h>

struct _pywm_callbacks {
    PyObject* motion;
    PyObject* motion_absolute;
    PyObject* button;
    PyObject* axis;
    PyObject* key;
    PyObject* modifiers;
};

#endif
