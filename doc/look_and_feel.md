# Look and feel

At this point you're wondering how you can customize the appearance of applications in newm.
Here's some help.
If you want to customize the appearance of newm itself,
[see the corresponding section in newm](./config.md#config-general-appearance)

## GTK settings

For this purpose, and for any command that does not need to remain listening, with newm we can write a function your config file that will be executed every time the newm configuration is restarted. The function is named `on_reconfigure`.

For defining a desktop theme and icons theme (among other things) we use [gsettings](https://wiki.gnome.org/HowDoI/GSettings). The implementation is as follows:

```python
def on_reconfigure():
    gnome_schema = 'org.gnome.desktop.interface'
    wm_service_extra_config = (
        f"gsettings set {gnome_schema} gtk-theme 'theme'",  # change to the theme of your choice
        f"gsettings set {gnome_schema} icon-theme 'icon'",  # change to the icon of your choice
        f"gsettings set {gnome_schema} cursor-theme 'cursors'",  # change to the cursor of your choice
        f"gsettings set {gnome_schema} font-name 'font'",  # change to the font of your choice
    )

    for config in wm_service_extra_config:
        config = f"{config} &"
        os.system(config)
```

Personally I like to add some extra settings(jbuchermn's personal config):

```python
def on_reconfigure():
    gnome_schema = 'org.gnome.desktop.interface'
    gnome_peripheral = 'org.gnome.desktop.peripherals'
    wm_service_extra_config = (
        f"gsettings set {gnome_schema} gtk-theme 'Sweet-Dark-v40'",
        f"gsettings set {gnome_schema} icon-theme 'candy-icons'",
        f"gsettings set {gnome_schema} cursor-theme 'Sweet-cursors'",
        f"gsettings set {gnome_schema} font-name 'Lucida MAC 11'",
        f"gsettings set {gnome_peripheral}.keyboard repeat-interval 30",
        f"gsettings set {gnome_peripheral}.keyboard delay 500",
        f"gsettings set {gnome_peripheral}.mouse natural-scroll false",
        f"gsettings set {gnome_peripheral}.mouse speed 0.0",
        f"gsettings set {gnome_peripheral}.mouse accel-profile 'default'",
        "gsettings set org.gnome.desktop.wm.preferences button-layout :",
    )

    for config in wm_service_extra_config:
        config = f"{config} &"
        os.system(config)
```

## Configuere Bar

### Native bar

newm has a built-in bar, whose main feature is simplicity. Here is a configuration that might be to your liking:

```python
import os
import pwd
import time
import psutil  #install
from subprocess import check_output
# the imports can be placed at the top of your configuration file

# install nmcli
ssid = "nmcli -t -f active,ssid dev wifi | egrep '^sí'\
    | cut -d\\: -f2"

# install brightnessctl
brightness = "brightnessctl i | grep 'Current' | cut -d\\( -f2"

volume = "awk -F\"[][]\" '/Left:/ { print $2 }' <(amixer sget Master)"


def get_nw():
    # Change for your interface
    ifdevice = "wlan0"
    ip = ""
    try:
        ip = psutil.net_if_addrs()[ifdevice][0].address
    except Exception:
        ip = "-/-"
    ssid_string = check_output(ssid, shell=True).decode("utf-8")
    return f"  {ifdevice}: {ssid_string[:-1]} / {ip}"


bar = {
    'font': 'JetBrainsMono Nerd Font',
    'font_size': 15,
    'height': 20,
    'top_texts': lambda: [
        pwd.getpwuid(os.getuid())[0],
        f" {psutil.cpu_percent(interval=1)}",
        f" {psutil.virtual_memory().percent}%",
        f"/ {psutil.disk_usage('/').percent}%\
            /home {psutil.disk_usage('/home').percent}%"
    ],
    'bottom_texts': lambda: [
        f'{psutil.sensors_battery().percent} \
            {"↑" if psutil.sensors_battery().power_plugged else "↓"}',
        f' {check_output(brightness, shell=True).decode("utf-8")[:-2]}',
        f'墳 {check_output(volume, shell=True).decode("utf-8")[:-1]}',
        get_nw(),
        f' {time.strftime("%c")}'
    ]
}
```

note: If you have any other native bar settings add them to this file and make a pr

### Another bar

Maybe the native bar doesn't meet your needs or you need more interactivity or just want to have a tray on the bar.
Whatever the reason you don't want the native bar, newm can disable it and replace it with the one of your choice. In this case I will use waybar but you could use any bar, in any case you can copy the following and adapt it to your needs:

```python
# More config
def on_startup():
    # More services
    os.system("waybar &")

bar = {'enabled': False}
```
(end)
