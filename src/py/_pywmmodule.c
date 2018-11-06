#define _POSIX_C_SOURCE 200112L

#include <Python.h>
#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
#include "wm.h"

static PyObject* _pywm_run(PyObject* self, PyObject* args){
    wm_init();
    int status = wm_run();

    return Py_BuildValue("i", status);
}

static PyObject* _pywm_terminate(PyObject* self, PyObject* args){
    wm_terminate();
    wm_destroy();

    return Py_BuildValue("i", 0);
}

static PyMethodDef _pywm_methods[] = {
    { "run",        &_pywm_run,     METH_VARARGS,   "Start the compoitor"  },
    { "terminate",  &_pywm_terminate,     METH_VARARGS,   "Start the compoitor"  },
    { NULL,   NULL,           0,              NULL                   }
};

static struct PyModuleDef _pywm = {
    PyModuleDef_HEAD_INIT,
    "_pywm",
    "",
    -1,
    _pywm_methods
};

PyMODINIT_FUNC PyInit__pywm(void){
    return PyModule_Create(&_pywm);
}
