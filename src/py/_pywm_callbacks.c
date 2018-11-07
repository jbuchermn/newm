#define _POSIX_C_SOURCE 200112L

#include <Python.h>
#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
#include <wlr/util/log.h>
#include "wm.h"
#include "_pywm_callbacks.h"
#include "_pywm_view.h"

static struct _pywm_callbacks callbacks = { 0 };

/*
 * Helpers
 */
static bool call_bool(PyObject* callable, PyObject* args){
    PyGILState_STATE gil = PyGILState_Ensure();
    PyObject *_result = PyEval_CallObject(callable, args);
    PyGILState_Release(gil);

    /* Py_XDECREF(args); */
    bool result = false;
    if(!_result || _result == Py_None || !PyArg_Parse(_result, "b", &result)){
        wlr_log(WLR_DEBUG, "Python error: Expected boolean return");
    }
    Py_XDECREF(_result);

    return result;
}

static void call_void(PyObject* callable, PyObject* args){
    PyGILState_STATE gil = PyGILState_Ensure();
    PyObject *_result = PyEval_CallObject(callable, args);
    PyGILState_Release(gil);

    /* Py_XDECREF(args); */
    if(!_result){
        wlr_log(WLR_DEBUG, "Python error: Exception thrown");
    }
    Py_XDECREF(_result);
}

/*
 * Callbacks
 */
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

static void call_init_view(struct wm_view* view){
    if(callbacks.init_view){
        long handle = _pywm_views_add(view);
        PyObject* args = Py_BuildValue("(l)", handle);
        call_void(callbacks.init_view, args);
    }
}

static void call_destroy_view(struct wm_view* view){
    if(callbacks.destroy_view){
        long handle = _pywm_views_remove(view);
        PyObject* args = Py_BuildValue("(l)", handle);
        call_void(callbacks.destroy_view, args);
    }
}

/*
 * Public interface
 */
void _pywm_callbacks_init(){
    get_wm()->callback_key = &call_key;
    get_wm()->callback_modifiers = &call_modifiers;
    get_wm()->callback_motion = &call_motion;
    get_wm()->callback_motion_absolute = &call_motion_absolute;
    get_wm()->callback_button = &call_button;
    get_wm()->callback_axis = &call_axis;
    get_wm()->callback_init_view = &call_init_view;
    get_wm()->callback_destroy_view = &call_destroy_view;
}

PyObject** _pywm_callbacks_get(const char* name){
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
    }else if(!strcmp(name, "init_view")){
        return &callbacks.init_view;
    }else if(!strcmp(name, "destroy_view")){
        return &callbacks.destroy_view;
    }

    return NULL;
}
