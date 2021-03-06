# NeWM - PyWM reference implementation

## Installing and running

Install greetd, make wlroots compile.

```
sudo pip3 install -v git+https://github.com/jbuchermn/pywm

git clone https://github.com/jbuchermn/newm
cd newm

# TODO: Proper configuration
vim newm/run.py

sudo pip3 install -v .

# TODO: Proper installation
cd panel
sudo npm install -g nw --unsafe-perm
sudo cp -r . /usr/lib/node_modules/newm-panel

start-newm
```

