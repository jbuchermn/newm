### Integration with systemd

It is likely that you are a systemd user, and you want newm to integrate with
it. For this purpose you should add the following in your configuration file,
in the on_startup function:

``` python
def on_startup():
		os.system("systemctl --user import-environment DISPLAY WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")
		os.system("hash dbus-update-activation-environment 2>/dev/null && \
				dbus-update-activation-environment --systemd DISPLAY \
				WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")
```

With this, systemd and newm are seamlessly integrated.

Note: if you did not follow [this](./env_wayland.md) add `=wlroots` to `XDG_CURRENT_DESKTOP`

`newm-cmd lock` can be used to achieve locking on hibernate in order to have the computer restart in a locked state by placing the following in e.g. `/lib/systemd/system-sleep/00-lock.sh`

``` sh
#!/bin/sh
/usr/[local/]/bin/newm-cmd lock-$1
```

Depending on installation process this might not work right ahead, as`systemd` runs these scripts in a clean environment as `root`. To check:

``` sh
su root
env -i /usr/[local/]bin/newm-cmd lock-pre
```
