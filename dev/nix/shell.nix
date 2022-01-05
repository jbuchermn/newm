{ pkgs, pywm }:
let
  my-python = pkgs.python3;
  python-with-my-packages = my-python.withPackages (p: with p; [
    pywm
    pycairo
    psutil
    websockets
    python-pam
    pyfiglet
    fuzzywuzzy
  ]);
in
with pkgs;
mkShell {
  buildInputs = [
    python-with-my-packages
  ];
}
