#define _POSIX_C_SOURCE 200112L

#include <Python.h>
#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
#include <wlr/util/log.h>
#include "wm/wm.h"
#include "wm/wm_layout.h"
#include "py/_pywm_callbacks.h"
#include "py/_pywm_view.h"

static struct _pywm_callbacks callbacks = { 0 };

/*
 * Helpers
 */
static bool call_bool(PyObject* callable, PyObject* args){
    PyGILState_STATE gil = PyGILState_Ensure();
    PyObject *_result = PyEval_CallObject(callable, args);
    Py_XDECREF(args); // Needs to happen inside lock
    PyGILState_Release(gil);

    int result = false;
    if(!_result || _result == Py_None || !PyArg_Parse(_result, "b", &result)){
        wlr_log(WLR_DEBUG, "Python error: Expected boolean return");
    }
    Py_XDECREF(_result);

    return result;
}

static void call_void(PyObject* callable, PyObject* args){
    PyGILState_STATE gil = PyGILState_Ensure();
    PyObject *_result = PyEval_CallObject(callable, args);
    Py_XDECREF(args);
    PyGILState_Release(gil);

    if(!_result){
        wlr_log(WLR_DEBUG, "Python error: Exception thrown");
    }
    Py_XDECREF(_result);
}

/*
 * Callbacks
 */
static void call_layout_change(struct wm_layout* layout){
    if(callbacks.layout_change){
        struct wlr_box* box = wlr_output_layout_get_box(layout->wlr_output_layout, NULL);
        PyObject* args = Py_BuildValue("(ii)", box->width, box->height);
        call_void(callbacks.layout_change, args);
    }
}

static bool call_key(struct wlr_event_keyboard_key* event){
    if(callbacks.key){
        PyObject* args = Py_BuildValue("(iii)", event->time_msec, event->keycode, event->state);
        return call_bool(callbacks.key, args);
    }

    return false;
}

static bool call_modifiers(struct wlr_keyboard_modifiers* modifiers){
    if(callbacks.modifiers){
        PyObject* args = Py_BuildValue("(iiii)", modifiers->depressed, modifiers->latched, modifiers->locked, modifiers->group);
        return call_bool(callbacks.modifiers, args);
    }

    return false;
}

static bool call_motion(double delta_x, double delta_y, uint32_t time_msec){
    if(callbacks.motion){
        PyObject* args = Py_BuildValue("(idd)", time_msec, delta_x, delta_y);
        return call_bool(callbacks.motion, args);
    }

    return false;
}

static bool call_motion_absolute(double x, double y, uint32_t time_msec){
    if(callbacks.motion_absolute){
        PyObject* args = Py_BuildValue("(idd)", time_msec, x, y);
        return call_bool(callbacks.motion_absolute, args);
    }

    return false;
}

static bool call_button(struct wlr_event_pointer_button* event){
    if(callbacks.button){
        PyObject* args = Py_BuildValue("(iii)", event->time_msec, event->button, event->state);
        return call_bool(callbacks.button, args);
    }

    return false;
}

static bool call_axis(struct wlr_event_pointer_axis* event){
    if(callbacks.axis){
        PyObject* args = Py_BuildValue("(iiidi)", event->time_msec, event->source, event->orientation,
                event->delta, event->delta_discrete);
        return call_bool(callbacks.axis, args);
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
    get_wm()->callback_layout_change = &call_layout_change;
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
    }else if(!strcmp(name, "layout_change")){
        return &callbacks.layout_change;
    }

    return NULL;
}
