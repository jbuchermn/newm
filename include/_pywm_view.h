#ifndef _PYWM_VIEW_H
#define _PYWM_VIEW_H

#include <Python.h>

struct wm_view;

struct _pywm_view {
    long handle;
    struct wm_view* view;

    struct _pywm_view* next_view;
};

void _pywm_view_init(struct _pywm_view* _view, struct wm_view* view);

struct _pywm_views {
    struct _pywm_view* first_view;
};

void _pywm_views_init();
long _pywm_views_add(struct wm_view* view);
long _pywm_views_remove(struct wm_view* view);

struct wm_view* _pywm_views_from_handle(long handle);

/*
 * Python functions
 */
PyObject* _pywm_view_get_box(PyObject* self, PyObject* args);
PyObject* _pywm_view_get_dimensions(PyObject* self, PyObject* args);
PyObject* _pywm_view_get_title_app_id(PyObject* self, PyObject* args);
PyObject* _pywm_view_set_box(PyObject* self, PyObject* args);
PyObject* _pywm_view_set_dimensions(PyObject* self, PyObject* args);


#endif
