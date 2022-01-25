{
  description = "newm - Wayland compositor";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    flake-utils.url = "github:numtide/flake-utils";

    pywmpkg.url = "github:jbuchermn/pywm/v0.3";
    pywmpkg.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, pywmpkg, flake-utils }:
  flake-utils.lib.eachDefaultSystem (
    system:
    let
      pkgs = import nixpkgs {
        inherit system;
        overlays = [
          (self: super: rec {
            python3 = super.python3.override {
              packageOverrides = self1: super1: {
                pywm = pywmpkg.packages.${system}.pywm;
                dasbus = super1.buildPythonPackage rec {
                  pname = "dasbus";
                  version = "1.6";

                  src = super1.fetchPypi {
                    inherit pname version;
                    sha256 = "sha256-FJrY/Iw9KYMhq1AVm1R6soNImaieR+IcbULyyS5W6U0=";
                  };

                  setuptoolsCheckPhase = "true";

                  propagatedBuildInputs = with super1; [ pygobject3 ];
                };
              };
            };
            python3Packages = python3.pkgs;
          })
        ];
      };
    in
    {
      packages.newm =
        pkgs.python3.pkgs.buildPythonApplication rec {
          pname = "newm";
          version = "0.3alpha";

          src = ./.;

          propagatedBuildInputs = with pkgs.python3Packages; [
            pywm
            pycairo
            psutil
            python-pam
            pyfiglet
            fuzzywuzzy
            dasbus
          ];

          setuptoolsCheckPhase = "true";
        };

      devShell = let
        my-python = pkgs.python3;
        python-with-my-packages = my-python.withPackages (ps: with ps; [
          pywm
          pycairo
          psutil
          python-pam
          pyfiglet
          fuzzywuzzy
          dasbus

          python-lsp-server
          pylsp-mypy
          mypy
          yappi
        ]);
      in
        pkgs.mkShell {
          buildInputs = [ python-with-my-packages ];
        };
    }
  );
}
