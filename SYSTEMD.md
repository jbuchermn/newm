# Integration with systemd

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

note: if you did not follow the [env_wayland](./SYSTEMD.md) add =wlroots to `XDG_CURRENT_DESKTOP`
