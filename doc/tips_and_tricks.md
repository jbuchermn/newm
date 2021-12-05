### Tips and Tricks

This section lists some tips and tricks you can use to make your day-to-day work with newm and wayland easier. If you know of any other useful tips and tricks open a pr.


#### Open any electron application natively with wayland

This trick consists of simply creating a script that passes the necessary flags to it so that it opens natively with wayland.
The script is as follows `/usr/loacal/open-wl`:
``` bash
#!/usr/bin/env bash

flags='--enable-features=UseOzonePlatform \
--ozone-platform=wayland'
$1 $flags $2
```

usage:

``` bash
$ open-wl brave
```

personally I like to add other additional banners to enhance the experience.
Below is my script:

``` bash
#!/usr/bin/env bash

flags='--enable-features=UseOzonePlatform \
--ozone-platform=wayland \
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
