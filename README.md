# NeWM - PyWM reference implementation

## Installing and running

Install greetd, make wlroots compile.

### newm

Sudo installation is only necessary in case greetd should run newm

```
sudo pip3 install -v git+https://github.com/jbuchermn/pywm

git clone https://github.com/jbuchermn/newm
cd newm

# TODO: Proper configuration
vim newm/run.py

sudo pip3 install -v .
start-newm
```

### Panel

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
