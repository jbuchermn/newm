project(
    'pywm',
    'c',
    version: '0.1.0',
    license: 'MIT',
    meson_version: '>=0.48.0',
    default_options : [
        'c_std=c11',
        'warning_level=2'
    ],
)

python = import('python').find_installation('python3')

wlroots_proj = subproject('wlroots')

# Dependencies
wlroots     = wlroots_proj.get_variable('wlroots')
wlr_protos  = wlroots_proj.get_variable('wlr_protos')
pixman      = dependency('pixman-1')
pthread     = meson.get_compiler('c').find_library('pthread')

deps = [wlroots, wlr_protos, pixman, pthread]

add_project_arguments(
	'-DWLR_USE_UNSTABLE',
	language: 'c',
)

add_project_arguments(
	'-Wno-unused-parameter',
	language: 'c',
)

sources = [
    'src/wm/wm.c',
    'src/wm/wm_server.c',
    'src/wm/wm_seat.c',
    'src/wm/wm_keyboard.c',
    'src/wm/wm_pointer.c',
    'src/wm/wm_cursor.c',
    'src/wm/wm_layout.c',
    'src/wm/wm_output.c',
    'src/wm/wm_view.c',
]

py_sources = [
    'src/py/_pywmmodule.c'
]

incs = include_directories('include')

executable(
	'pywm',
	sources + ['src/main.c'],
    include_directories: incs,
	dependencies: deps,
)

python.extension_module(
    '_pywm',
    sources + py_sources,
    include_directories: incs,
    dependencies: deps + [python.dependency()]
)
