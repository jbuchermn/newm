# newm - beyond tiling
(Wayland compositor)
![IMAGE](https://github.com/jbuchermn/newm/blob/v0.1/resources/screenshot.png)](https://youtu.be/otMEC03ie0g)

## Installing

### Prerequisites and pywm

See [pywm](https://github.com/jbuchermn/pywm). If all prerequisites are installed, the command:

```
pip3 install git+https://github.com/jbuchermn/pywm
```

should suffice.


### Single-user installation (without newm-login)

To install newm:

```
pip3 install git+https://github.com/jbuchermn/newm
```

Start it using

```
start-newm
```


### Multi-user installation with greetd (to use newm for login)

Make sure to also install pywm using sudo:

```
sudo pip3 install git+https://github.com/jbuchermn/pywm
sudo pip3 install git+https://github.com/jbuchermn/newm
```

Check, after logging in as `greeter`, that `start-newm` works and show the login panel. If it works, set

```
command = "start-newm"
```

in `/etc/greetd/config.toml` and ensure configuration is set in `/etc/newm/config.py`

## Panel

See [newm-panel-nwjs](https://github.com/jbuchermn/newm-panel-nwjs)


### greetd

Set

```
command = "start-newm"
```

in `/etc/greetd/config.toml` and ensure configuration is set in `/etc/newm/config.py`

### Lock on hibernate

Place in `/lib/systemd/system-sleep/00-lock.sh`

```
#!/bin/sh
newm-cmd lock-$1 
```
