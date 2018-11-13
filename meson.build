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

add_project_arguments(
	'-Wno-unused-parameter',
	language: 'c',
)

add_project_arguments(
	'-DWLR_USE_UNSTABLE',
	language: 'c',
)

add_project_arguments(
	'-DPYWM_NO_XWAYLAND',
	language: 'c',
)



# Dependencies
wlroots        = dependency('wlroots')
wayland_server = dependency('wayland-server')
wayland_client = dependency('wayland-client')
wayland_cursor = dependency('wayland-cursor')
wayland_egl    = dependency('wayland-egl')
wayland_protos = dependency('wayland-protocols', version: '>=1.14')
xkbcommon      = dependency('xkbcommon')
pixman         = dependency('pixman-1')
pthread        = meson.get_compiler('c').find_library('pthread')
math           = meson.get_compiler('c').find_library('m')


subdir('protocols')


deps = [
    wlroots,
    wayland_server,
    server_protos,
    xkbcommon,
    pixman,
    pthread,
    math
]


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
    'src/wm/wm_widget.c',
]

py_sources = [
    'src/py/_pywmmodule.c',
    'src/py/_pywm_callbacks.c',
    'src/py/_pywm_view.c',
    'src/py/_pywm_widget.c'
]

incs = include_directories('include')

executable(
	'pywm',
	sources + ['src/main.c'],
    include_directories: incs,
	dependencies: deps,
)

python = import('python').find_installation('python3')

python.extension_module(
    '_pywm',
    sources + py_sources,
    include_directories: incs,
    dependencies: deps + [python.dependency()]
)
