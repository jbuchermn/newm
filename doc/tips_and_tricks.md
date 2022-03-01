# Tips and Tricks

This section lists some tips and tricks you can use to make your day-to-day work with newm and wayland easier. If you know of any other useful tips and tricks open a pr.

## Open any electron application natively with wayland

This trick consists of simply creating a script that passes the necessary flags to it so that it opens natively with wayland.
The script is as follows `/usr/loacal/open-wl`:

```bash
#!/usr/bin/env bash

flags=--ozone-platform-hint=auto'
$1 $flags $2
```

usage:

```bash
$ open-wl brave
```

personally I like to add other additional flags to enhance the experience.
Below is my script:

```bash
#!/usr/bin/env bash

flags='--ozone-platform-hint=auto \
--enable-features=WebRTCPipeWireCapturer \
--enable-gpu \
--ignore-gpu-blocklist \
--enable-gpu-rasterization \
--enable-zero-copy \
--disable-gpu-driver-bug-workarounds \
--enable-features=VaapiVideoDecoder \
--disable-software-rasterizer \
--start-maximized \
--js-flags="--max-old-space-size=5120"'

$1 $flags $2
```

Ideally, all electron applications should read the electrom-flags.conf file, but as long as this is not a standard, this will be of great help.

You can improve this trick by modifying or creating the .desktop files that you
want to open natively.

## Change wallpaper when reconfigure

this trick is quite simple and consists only in creating a folder with numbered images, below I show an example of how to call these images randomly every time you reconfigure the system:

newm config:

```python
background = {
    "path": os.environ["HOME"] + f"/images/random/bg-{randrange(1, 5)}.jpg",
    "time_scale": 0.125,
    "anim": True,
}
```

## Python

The simple fact of using python to configure is already a trick in itself. Below I will list a set of code snippets that will make your configuration cleaner.The simple fact of using python to configure is already a trick in itself. Below I will list a set of code snippets that will make your configuration cleaner.

### Use tuples in your startup applications

Example:

```python
def on_startup():
    init_service = (
        "/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1",
        "systemctl --user import-environment \
        DISPLAY WAYLAND_DISPLAY XDG_CURRENT_DESKTOP",
        "hash dbus-update-activation-environment 2>/dev/null && \
        dbus-update-activation-environment --systemd \
        DISPLAY WAYLAND_DISPLAY XDG_CURRENT_DESKTOP",
        "wl-paste -t text --watch clipman store",
        "wlsunset -l 16.0867 -L -93.7561 -t 2500 -T 6000",
        "thunar --daemon",
        "waybar",
        "nm-applet --indicator",
        "/home/crag/Git/dotfiles/etc/dnscrypt-proxy/get_blocklist",
    )

    for service in init_service:
        service = f"{service} &"
        os.system(service)
```

### Use variables for your repetitive rules

Example:

```python
def rules(view):
    common_rules = {"float": True, "float_size": (750, 750), "float_pos": (0.5, 0.35)}
    float_apps = ("pavucontrol", "blueman-manager") #applications that I want to define as floating
    blur_apps = ("kitty", "rofi", "waybar") # applications in which I want to have the blur effect
    if view.app_id in float_apps:
        return common_rules
    if view.app_id in blur_apps:
        return {"blur": {"radius": 6, "passes": 4}}
    return None
```
