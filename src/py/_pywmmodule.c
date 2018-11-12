#include <Python.h>
#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
#include <wlr/util/log.h>
#include "wm/wm.h"
#include "py/_pywm_callbacks.h"
#include "py/_pywm_view.h"


static PyObject* _pywm_run(PyObject* self, PyObject* args){
    wm_init();
    _pywm_callbacks_init();

    int status = wm_run();

    return Py_BuildValue("i", status);
}

static PyObject* _pywm_join(PyObject* self, PyObject* args){
    wm_join();

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject* _pywm_terminate(PyObject* self, PyObject* args){
    wm_terminate();
    wm_destroy();

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject* _pywm_register(PyObject* self, PyObject* args){
    const char* name;
    PyObject* callback;

    if(!PyArg_ParseTuple(args, "sO", &name, &callback)){
        PyErr_SetString(PyExc_TypeError, "Invalid parameters");
        return NULL;
    }

    if(!PyCallable_Check(callback)){
        PyErr_SetString(PyExc_TypeError, "Object is not callable");
        return NULL;
    }
    
    PyObject** target = _pywm_callbacks_get(name);
    if(!target){
        PyErr_SetString(PyExc_TypeError, "Unknown callback");
        return NULL;
    }

    Py_XDECREF(*target);
    *target = callback;
    Py_INCREF(*target);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyMethodDef _pywm_methods[] = {
    { "run",                    &_pywm_run,                    METH_VARARGS,   "Start the compoitor in a new thread" },
    { "join",                   &_pywm_join,                   METH_VARARGS,   "Join compositor thread"  },
    { "terminate",              &_pywm_terminate,              METH_VARARGS,   "Terminate compositor and join"  },
    { "register",               &_pywm_register,               METH_VARARGS,   "Register callback"  },
    { "view_get_box",           &_pywm_view_get_box,           METH_VARARGS,   "" },
    { "view_get_dimensions",    &_pywm_view_get_dimensions,    METH_VARARGS,   "" },
    { "view_get_title_app_id",  &_pywm_view_get_title_app_id,  METH_VARARGS,   "" },
    { "view_set_box",           &_pywm_view_set_box,           METH_VARARGS,   "" },
    { "view_set_dimensions",    &_pywm_view_set_dimensions,    METH_VARARGS,   "" },
    { "view_focus",             &_pywm_view_focus,             METH_VARARGS,   "" },

    { NULL, NULL, 0, NULL }
};

static struct PyModuleDef _pywm = {
    PyModuleDef_HEAD_INIT,
    "_pywm",
    "",
    -1,
    _pywm_methods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyMODINIT_FUNC PyInit__pywm(void){
    return PyModule_Create(&_pywm);
}
