#define _POSIX_C_SOURCE 200112L

#include <Python.h>
#include <assert.h>
#include <stdlib.h>
#include <unistd.h>

#include "_pywm_view.h"
#include "wm_view.h"

static struct _pywm_views views = { 0 };

void _pywm_view_init(struct _pywm_view* _view, struct wm_view* view){
    static long handle = 0;
    handle++;

    _view->handle = handle;
    _view->view = view;
    _view->next_view = NULL;
}

long _pywm_views_add(struct wm_view* view){
    struct _pywm_view* it;
    for(it = views.first_view; it && it->next_view; it=it->next_view);
    struct _pywm_view** insert;
    if(it){
        insert = &it->next_view;
    }else{
        insert = &views.first_view;
    }

    *insert = malloc(sizeof(struct _pywm_view));
    _pywm_view_init(*insert, view);
    return (*insert)->handle;
}

long _pywm_views_remove(struct wm_view* view){
    struct _pywm_view* remove;
    if(views.first_view && views.first_view->view == view){
        remove = views.first_view;
        views.first_view = remove->next_view;
    }else{
        struct _pywm_view* prev;
        for(prev = views.first_view; prev && prev->next_view && prev->next_view->view != view; prev=prev->next_view);
        assert(prev);

        remove = prev->next_view;
        prev->next_view = remove->next_view;
    }

    assert(remove);
    long handle = remove->handle;
    free(remove);

    return handle;
}

struct wm_view* _pywm_views_from_handle(long handle){
    for(struct _pywm_view* view = views.first_view; view; view=view->next_view){
        if(view->handle == handle) return view->view;
    }

    return NULL;
}

PyObject* _pywm_view_get_box(PyObject* self, PyObject* args){
    long handle;
    if(!PyArg_ParseTuple(args, "l", &handle)){
        PyErr_SetString(PyExc_TypeError, "Arguments");
        return NULL;
    }

    struct wm_view* view = _pywm_views_from_handle(handle);
    if(!view){
        PyErr_SetString(PyExc_TypeError, "View has been destroyed");
        return NULL;
    }

    return Py_BuildValue("(dddd)", view->display_x, view->display_y, view->display_height, view->display_width);
}

PyObject* _pywm_view_get_dimensions(PyObject* self, PyObject* args){
    long handle;
    if(!PyArg_ParseTuple(args, "l", &handle)){
        PyErr_SetString(PyExc_TypeError, "Arguments");
        return NULL;
    }

    struct wm_view* view = _pywm_views_from_handle(handle);
    if(!view){
        PyErr_SetString(PyExc_TypeError, "View has been destroyed");
        return NULL;
    }

    int width, height;
    wm_view_get_size(view, &width, &height);

    return Py_BuildValue("(ii)", width, height);

}

PyObject* _pywm_view_get_title_app_id(PyObject* self, PyObject* args){
    long handle;
    if(!PyArg_ParseTuple(args, "l", &handle)){
        PyErr_SetString(PyExc_TypeError, "Arguments");
        return NULL;
    }

    struct wm_view* view = _pywm_views_from_handle(handle);
    if(!view){
        PyErr_SetString(PyExc_TypeError, "View has been destroyed");
        return NULL;
    }

    return Py_BuildValue("(ss)", view->title, view->app_id);

}

PyObject* _pywm_view_set_box(PyObject* self, PyObject* args){
    long handle;
    double x, y, width, height;
    if(!PyArg_ParseTuple(args, "ldddd", &handle, &x, &y, &width, &height)){
        PyErr_SetString(PyExc_TypeError, "Arguments");
        return NULL;
    }

    struct wm_view* view = _pywm_views_from_handle(handle);
    if(!view){
        PyErr_SetString(PyExc_TypeError, "View has been destroyed");
        return NULL;
    }

    view->display_x = x;
    view->display_y = y;
    view->display_width = width;
    view->display_height = height;

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* _pywm_view_set_dimensions(PyObject* self, PyObject* args){
    long handle;
    int width, height;
    if(!PyArg_ParseTuple(args, "lii", &handle, &width, &height)){
        PyErr_SetString(PyExc_TypeError, "Arguments");
        return NULL;
    }

    struct wm_view* view = _pywm_views_from_handle(handle);
    if(!view){
        PyErr_SetString(PyExc_TypeError, "View has been destroyed");
        return NULL;
    }

    wm_view_request_size(view, width, height);

    Py_INCREF(Py_None);
    return Py_None;
}

