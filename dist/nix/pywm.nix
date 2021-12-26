# { lib, fetchFromGitHub, python3Packages, file, less, highlight
# , imagePreviewSupport ? true, w3m }:
with import <nixpkgs> {};

python3Packages.buildPythonPackage rec {
  pname = "pywm";
  version = "0.2";

  src = fetchFromGitHub {
    owner = "jbuchermn";
    repo = "pywm";
    fetchSubmodules = true;
    rev = "89f8de6";
    sha256= "sha256-UOBlV/I3f9XLHeKnF9EOYN7XpcHDpNC01mvRHOWJ4TQ=";
  };

  nativeBuildInputs = [
    meson_0_60
    ninja
    pkg-config
    wayland-scanner
    glslang
  ];

  dontUseMesonConfigure = true;

  buildInputs = [
    libGL
    wayland
    wayland-protocols
    libinput
    libxkbcommon
    mesa
    pixman
    seatd
    vulkan-loader
    xorg.xcbutilwm
    xorg.xcbutilrenderutil
    xorg.xcbutilerrors
    xwayland
  ];

  propagatedBuildInputs = [
    python3.pkgs.imageio
    python3.pkgs.numpy
    python3.pkgs.pycairo
    python3.pkgs.evdev
    python3.pkgs.matplotlib
  ];

  LC_ALL = "en_US.UTF-8";

  meta =  with lib; {
    description = "Wayland compositor core";
    homepage = "https://github.com/jbuchermn/pywm";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
