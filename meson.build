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

wlroots_proj = subproject('wlroots')

# Dependencies
wlroots     = wlroots_proj.get_variable('wlroots')
wlr_protos  = wlroots_proj.get_variable('wlr_protos')
pixman      = dependency('pixman-1')

add_project_arguments(
	'-DWLR_USE_UNSTABLE',
	language: 'c',
)

add_project_arguments(
	'-Wno-unused-parameter',
	language: 'c',
)

sources = [
    'src/wm_server.c',
    'src/wm_seat.c',
    'src/wm_keyboard.c',
    'src/wm_pointer.c',
    'src/wm_cursor.c',
    'src/wm_layout.c',
    'src/wm_output.c',
    'src/wm_view.c',
    'src/main.c',
]

incs = include_directories('include')

executable(
	'pywm',
	sources,
    include_directories: incs,
	dependencies: [wlroots, wlr_protos, pixman],
)
