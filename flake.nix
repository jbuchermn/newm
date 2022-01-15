{
  description = "newm - Wayland compositor";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    flake-utils.url = "github:numtide/flake-utils";

    pywm.url = "github:jbuchermn/pywm/v0.3";
    pywm.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, pywm, flake-utils }:
  flake-utils.lib.eachDefaultSystem (
    system:
    let
      pkgs = nixpkgs.legacyPackages.${system}; 
      pywmpkg = pywm.packages.${system};
      dasbuspkg = {
        dasbus = pkgs.python3.pkgs.buildPythonPackage rec {
          pname = "dasbus";
          version = "1.6";

          src = pkgs.python3.pkgs.fetchPypi {
            inherit pname version;
            sha256 = "sha256-FJrY/Iw9KYMhq1AVm1R6soNImaieR+IcbULyyS5W6U0=";
          };

          setuptoolsCheckPhase = "true";

          propagatedBuildInputs = with pkgs.python3Packages; [ pygobject3 ];
        };

      };
    in
    {
      packages.newm =
        pkgs.python3.pkgs.buildPythonApplication rec {
          pname = "newm";
          version = "0.3alpha";

          src = ./.;

          propagatedBuildInputs = with pkgs.python3Packages; [
            pywmpkg.pywm
            pycairo
            psutil
            python-pam
            pyfiglet
            fuzzywuzzy
            dasbuspkg.dasbus
          ];

          setuptoolsCheckPhase = "true";
        };

      devShell = let
        my-python = pkgs.python3;
        python-with-my-packages = my-python.withPackages (ps: with ps; [
          pywmpkg.pywm
          pycairo
          psutil
          python-pam
          pyfiglet
          fuzzywuzzy
          dasbuspkg.dasbus

          python-lsp-server
          pylsp-mypy
          mypy
        ]);
      in
        pkgs.mkShell {
          buildInputs = [ python-with-my-packages ];
        };
    }
  );
}
