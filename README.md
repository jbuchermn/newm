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

### newm-panel

Sudo installation is only necessary in case greetd should run newm / otherwise `npm run build-...` together with proper config (see above) is sufficient.

```
cd newm/panel

sudo npm install -g nw --unsafe-perm
# TODO: Proper installation
sudo ./install_unsafe.sh

start-newm
```

### greetd

Set

```
command = "start-newm"
```

in `/etc/greetd/config.toml`

### Lock on hibernate

Place in `/lib/systemd/system-sleep/00-lock.sh`

```
#!/bin/sh
newm-cmd lock 
```
