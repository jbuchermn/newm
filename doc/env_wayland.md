### Setting environment variables for a wayland session

It is very likely that you want to have newm configured as well as possible and that it is not the only wm you have installed. In this context it is helpful to have perfectly assigned environment variables for wayland integration with applications.


In case you use another wm or other wm's besides newm, maybe this bash script will be useful to assign environment variables and call them from different startup scripts.

 This script should preferably be saved under the following name `/usr/local/bin/wayland_enablement.sh`
 The content is shown below:

 ``` bash
 #!/bin/sh

#
# GTK environment
#

#export GDK_BACKEND=wayland # May cause problems with some xorg applications
export TDESKTOP_DISABLE_GTK_INTEGRATION=1
export CLUTTER_BACKEND=wayland
export BEMENU_BACKEND=wayland

# Firefox
export MOZ_ENABLE_WAYLAND=1

#
# Qt environment
#
export QT_QPA_PLATFORM=wayland-egl #error with apps xcb
export QT_WAYLAND_FORCE_DPI=physical
export QT_WAYLAND_DISABLE_WINDOWDECORATION=1

#
# Elementary environment
#
export ELM_DISPLAY=wl
export ECORE_EVAS_ENGINE=wayland_egl
export ELM_ENGINE=wayland_egl
export ELM_ACCEL=opengl
# export ELM_SCALE=1

#
# SDL environment
#
export SDL_VIDEODRIVER=wayland

#
# Java environment
#
export _JAVA_AWT_WM_NONREPARENTING=1

export NO_AT_BRIDGE=1
export WINIT_UNIX_BACKEND=wayland
export DBUS_SESSION_BUS_ADDRESS
export DBUS_SESSION_BUS_PID
 ```
 You can add more variables related to wayland integration with applications. If you do not know any of these variables you can search for information individually by variable name.


### Starting newm with environment variables

For this purpose it is necessary to add some variables related to the session,
then we will create the following script `/usr/local/bin/newm-run.sh`

 The content is shown below:

 ``` bash
#!/bin/sh

# Session
export XDG_SESSION_TYPE=wayland
export XDG_SESSION_DESKTOP=wlroots
export XDG_CURRENT_DESKTOP=wlroots
export XDG_CURRENT_SESSION=wlroots
source /usr/local/bin/wayland_enablement.sh #we import the environment variables defined above

sleep 0.5;

start-newm
 ```

 will now use this script to start newm(remember to give it execution permissions).

#### Use with greetd and tuigreet

Change `command` to the following line in your greetd config

``` bash
command = "newm-run.sh"
```

### Reusing variables with another wm

#### sway example

 ``` bash
#!/bin/sh

# Session
export XDG_SESSION_TYPE=wayland
export XDG_SESSION_DESKTOP=sway
export XDG_CURRENT_DESKTOP=sway
export XDG_CURRENT_SESSION=sway

source /usr/local/bin/wayland_enablement.sh #we import the environment variables defined above

sleep 1;

systemd-cat --identifier=sway sway $@
 ```


### Using newm with systemd

[Link](./systemd.md)
