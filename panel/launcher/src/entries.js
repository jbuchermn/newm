import icon_chromium from "./icons/chromium.svg";
import icon_file from "./icons/file.svg";
import icon_firefox from "./icons/firefox.svg";
import icon_gimp from "./icons/gimp.svg";
import icon_spotify from "./icons/spotify.svg";
import icon_terminal from "./icons/terminal.svg";
import icon_vscodium from "./icons/vscodium.svg";
import icon_emacs from "./icons/emacs.svg";

const entries = [
    { 
        name: 'Chromium',
        icon: icon_chromium,
        cmd: 'chromium --enable-features=UseOzonePlatform --ozone-platform=wayland'
    },{
        name: 'Nautilus',
        icon: icon_file,
        cmd: 'nautilus'
    },{
        name: 'Firefox',
        icon: icon_firefox,
        cmd: 'MOZ_ENABLE_WAYLAND=1 firefox'
    },{
        name: 'GIMP',
        icon: icon_gimp,
        cmd: 'gimp-2.99'
    },{
        name: 'Spotify',
        icon: icon_spotify,
        cmd: 'DISPLAY=":0" spotify --force-device-scale-factor=2'
    },{
        name: 'Alacritty',
        icon: icon_terminal,
        cmd: 'alacritty'
    },{
        name: 'Termite',
        icon: icon_terminal,
        cmd: 'termite'
    },{
        name: 'VSCodium',
        icon: icon_vscodium,
        cmd: 'DISPLAY=":0" vscodium --force-device-scale-factor=2'
    },{
        name: 'Emacs',
        icon: icon_emacs,
        cmd: 'emacsclient -c -a "emacs"'
    }
];
export default entries;
