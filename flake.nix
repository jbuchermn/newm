{
  description = "newm - Wayland compositor";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    flake-utils.url = "github:numtide/flake-utils";

    pywmpkg.url = "github:jbuchermn/pywm";
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
                thefuzz = super1.buildPythonPackage rec {
                  pname = "thefuzz";
                  version = "0.19.0";

                  src = super1.fetchPypi {
                    inherit pname version;
                    sha256 = "sha256-b3Em2y8silQhKwXjp0DkX0KRxJfXXSB1Fyj2Nbt0qj0=";
                  };

                  propagatedBuildInputs = with super1; [ 
                    python-Levenshtein
                    pycodestyle
                  ];
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
          version = "0.2";

          src = ./.;

          propagatedBuildInputs = with pkgs.python3Packages; [
            pywm

            pycairo
            psutil
            python-pam
            pyfiglet
            thefuzz
            websockets

            setuptools
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
          thefuzz
          websockets

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
