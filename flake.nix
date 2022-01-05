{
  description = "newm - Wayland compositor";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.pywm.url = "github:jbuchermn/pywm";

  outputs = { self, nixpkgs, pywm, flake-utils }:
  flake-utils.lib.eachDefaultSystem (
    system:
    let
      pkgs = nixpkgs.legacyPackages.${system}; 
      pywmpkg = pywm.packages.${system};
    in
    {
      packages.newm =
        pkgs.python3.pkgs.buildPythonApplication rec {
          pname = "newm";
          version = "0.2";

          src = ./.;

          propagatedBuildInputs = with pkgs.python3Packages; [
            pywmpkg.pywm
            pycairo
            psutil
            websockets
            python-pam
            pyfiglet
            fuzzywuzzy
          ];

          setuptoolsCheckPhase = "true";
        };
      }
      );
    }
