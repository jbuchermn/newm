#include <Python.h>
#include <assert.h>
#include <stdlib.h>
#include <unistd.h>

#include "wm/wm.h"
#include "wm/wm_widget.h"
#include "py/_pywm_widget.h"

static struct _pywm_widgets widgets = { 0 };

void _pywm_widget_init(struct _pywm_widget* _widget, struct wm_widget* widget){
    static long handle = 0;
    handle++;

    _widget->handle = handle;
    _widget->widget = widget;
    _widget->next_widget = NULL;
}

long _pywm_widgets_add(struct wm_widget* widget){
    struct _pywm_widget* it;
    for(it = widgets.first_widget; it && it->next_widget; it=it->next_widget);
    struct _pywm_widget** insert;
    if(it){
        insert = &it->next_widget;
    }else{
        insert = &widgets.first_widget;
    }

    *insert = malloc(sizeof(struct _pywm_widget));
    _pywm_widget_init(*insert, widget);
    return (*insert)->handle;
}

long _pywm_widgets_remove(struct wm_widget* widget){
    struct _pywm_widget* remove;
    if(widgets.first_widget && widgets.first_widget->widget == widget){
        remove = widgets.first_widget;
        widgets.first_widget = remove->next_widget;
    }else{
        struct _pywm_widget* prev;
        for(prev = widgets.first_widget; prev && prev->next_widget && prev->next_widget->widget != widget; prev=prev->next_widget);
        assert(prev);

        remove = prev->next_widget;
        prev->next_widget = remove->next_widget;
    }

    assert(remove);
    long handle = remove->handle;
    free(remove);

    return handle;
}

struct _pywm_widget* _pywm_widgets_container_from_handle(long handle){

    for(struct _pywm_widget* widget = widgets.first_widget; widget; widget=widget->next_widget){
        if(widget->handle == handle) return widget;
    }

    return NULL;
}

struct wm_widget* _pywm_widgets_from_handle(long handle){
    struct _pywm_widget* widget = _pywm_widgets_container_from_handle(handle);
    if(!widget){
        return NULL;
    }

    return widget->widget;
}


PyObject* _pywm_widget_create(PyObject* self, PyObject* args){
    struct wm_widget* widget = wm_create_widget();
    long handle = _pywm_widgets_add(widget);

    return Py_BuildValue("l", handle);
}

PyObject* _pywm_widget_destroy(PyObject* self, PyObject* args){
    long handle;
    if(!PyArg_ParseTuple(args, "l", &handle)){
        PyErr_SetString(PyExc_TypeError, "Arguments");
        return NULL;
    }

    struct wm_widget* widget = _pywm_widgets_from_handle(handle);
    if(!widget){
        PyErr_SetString(PyExc_TypeError, "Widget has been destroyed");
        return NULL;
    }

    _pywm_widgets_remove(widget);
    wm_destroy_widget(widget);

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* _pywm_widget_set_box(PyObject* self, PyObject* args){
    long handle;
    double x, y, width, height;
    if(!PyArg_ParseTuple(args, "ldddd", &handle, &x, &y, &width, &height)){
        PyErr_SetString(PyExc_TypeError, "Arguments");
        return NULL;
    }

    struct wm_widget* widget = _pywm_widgets_from_handle(handle);
    if(!widget){
        PyErr_SetString(PyExc_TypeError, "Widget has been destroyed");
        return NULL;
    }

    wm_widget_set_box(widget, x, y, width, height);

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* _pywm_widget_set_layer(PyObject* self, PyObject* args){
    long handle;
    int layer;
    if(!PyArg_ParseTuple(args, "li", &handle, &layer)){
        PyErr_SetString(PyExc_TypeError, "Arguments");
        return NULL;
    }

    struct wm_widget* widget = _pywm_widgets_from_handle(handle);
    if(!widget){
        PyErr_SetString(PyExc_TypeError, "Widget has been destroyed");
        return NULL;
    }

    if(layer == 0){
        widget->layer = WM_WIDGET_BACK;
    }else if(layer == 1){
        widget->layer = WM_WIDGET_FRONT;
    }else{
        PyErr_SetString(PyExc_TypeError, "Unknown layer");
        return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* _pywm_widget_set_pixels(PyObject* self, PyObject* args){
    long handle;
    int format, stride, width, height;
    PyObject* data;
    if(!PyArg_ParseTuple(args, "liiiiS", &handle, &format, &stride, &width, &height, &data)){
        PyErr_SetString(PyExc_TypeError, "Arguments");
        return NULL;
    }

    struct _pywm_widget* widget = _pywm_widgets_container_from_handle(handle);
    if(!widget){
        PyErr_SetString(PyExc_TypeError, "Widget has been destroyed");
        return NULL;
    }

    widget->pixels_pending = true;
    widget->pixels.format = format;
    widget->pixels.stride = stride;
    widget->pixels.width = width;
    widget->pixels.height = height;
    widget->pixels.data = data;

    Py_INCREF(data);

    Py_INCREF(Py_None);
    return Py_None;
}

static void _pywm_widgets_update(){
    for(struct _pywm_widget* widget = widgets.first_widget; widget; widget=widget->next_widget){
        if(widget->pixels_pending){
            wm_widget_set_pixels(widget->widget,
                    widget->pixels.format,
                    widget->pixels.stride,
                    widget->pixels.width,
                    widget->pixels.height,
                    PyBytes_AsString(widget->pixels.data));

            widget->pixels_pending = false;
            Py_DECREF(widget->pixels.data);
            widget->pixels.data = NULL;
        }
    }
}

void _pywm_widgets_init_callbacks(){
    get_wm()->callback_widgets_update = &_pywm_widgets_update;
}
