{ pywmDir }:
with import <nixpkgs> {};
with python39Packages;
let
  pywm = import (pywmDir + /dev/nix/pywm.nix);
in
buildPythonApplication rec {
  pname = "newm";
  version = "0.2";

  src = ../..;

  propagatedBuildInputs = [
    pywm
    pycairo
    psutil
    websockets
    python-pam
    pyfiglet
    fuzzywuzzy
  ];

  # Skip this as it tries to start the compositor
  setuptoolsCheckPhase = "true";

  LC_ALL = "en_US.UTF-8";
}
