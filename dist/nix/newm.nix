# { lib, fetchFromGitHub, python3Packages, file, less, highlight
# , imagePreviewSupport ? true, w3m }:
with import <nixpkgs> {};
let 
  pywm = import ./pywm.nix;
in

python3Packages.buildPythonPackage rec {
  pname = "newm";
  version = "0.2";

  src = fetchFromGitHub {
    owner = "jbuchermn";
    repo = "newm";
    rev = "4932747";
    sha256 = "sha256-esqz+bQVzSPHrwMCPBCIP0CCSATzixGhoCzNIGGrBJA=";
  };

  buildInputs = [
    pywm
    python3.pkgs.pycairo
    python3.pkgs.psutil
    python3.pkgs.websockets
    python3.pkgs.python-pam
    python3.pkgs.pyfiglet
    python3.pkgs.fuzzywuzzy
  ];

  # Skip this as it tries to start the compositor
  setuptoolsCheckPhase = "true";

  LC_ALL = "en_US.UTF-8";

  meta =  with lib; {
    description = "Wayland compositor";
    homepage = "https://github.com/jbuchermn/newm";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
