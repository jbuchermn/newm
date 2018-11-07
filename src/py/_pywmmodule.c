#define _POSIX_C_SOURCE 200112L

#include <Python.h>
#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
#include <wlr/util/log.h>
#include "wm.h"
#include "_pywmmodule.h"

static struct _pywm_callbacks callbacks = { 0 };

static bool call_bool(PyObject* callable, PyObject* args){
    PyGILState_STATE gil = PyGILState_Ensure();
    PyObject *_result = PyEval_CallObject(callable, args);
    PyGILState_Release(gil);

    Py_XDECREF(args);
    bool result = false;
    if(!_result || _result == Py_None || !PyArg_Parse(_result, "b", &result)){
        wlr_log(WLR_DEBUG, "Python error: Expected boolean return");
    }
    Py_DECREF(_result);

    return result;
}

static bool call_key(struct wlr_event_keyboard_key* event){
    if(callbacks.key){
        return call_bool(callbacks.key, NULL);
    }

    return false;
}

static bool call_modifiers(struct wlr_keyboard_modifiers* modifiers){
    if(callbacks.modifiers){
        return call_bool(callbacks.modifiers, NULL);
    }

    return false;
}

static bool call_motion(double delta_x, double delta_y, uint32_t time_msec){
    if(callbacks.motion){
        return call_bool(callbacks.motion, NULL);
    }

    return false;
}

static bool call_motion_absolute(double x, double y, uint32_t time_msec){
    if(callbacks.motion_absolute){
        return call_bool(callbacks.motion_absolute, NULL);
    }

    return false;
}

static bool call_button(struct wlr_event_pointer_button* event){
    if(callbacks.button){
        return call_bool(callbacks.button, NULL);
    }

    return false;
}

static bool call_axis(struct wlr_event_pointer_axis* event){
    if(callbacks.axis){
        return call_bool(callbacks.axis, NULL);
    }

    return false;
}

void _pywm_init_callbacks(){
    get_wm()->callback_key = &call_key;
    get_wm()->callback_modifiers = &call_modifiers;
    get_wm()->callback_motion = &call_motion;
    get_wm()->callback_motion_absolute = &call_motion_absolute;
    get_wm()->callback_button = &call_button;
    get_wm()->callback_axis = &call_axis;
}

PyObject** _pywm_get_callback(const char* name){
    if(!strcmp(name, "motion")){
        return &callbacks.motion;
    }else if(!strcmp(name, "motion_absolute")){
        return &callbacks.motion_absolute;
    }else if(!strcmp(name, "button")){
        return &callbacks.button;
    }else if(!strcmp(name, "axis")){
        return &callbacks.axis;
    }else if(!strcmp(name, "key")){
        return &callbacks.key;
    }else if(!strcmp(name, "modifiers")){
        return &callbacks.modifiers;
    }

    return NULL;
}

static PyObject* _pywm_run(PyObject* self, PyObject* args){
    wm_init();
    _pywm_init_callbacks();

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
    
    PyObject** target = _pywm_get_callback(name);
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
    { "run",        &_pywm_run,        METH_VARARGS,   "Start the compoitor in a new thread"  },
    { "join",       &_pywm_join,       METH_VARARGS,   "Join compositor thread"  },
    { "terminate",  &_pywm_terminate,  METH_VARARGS,   "Terminate compositor and join"  },
    { "register",   &_pywm_register,   METH_VARARGS,   "Register callback" },

    { NULL, NULL, 0, NULL }
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
