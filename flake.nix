{
  description = "newm - Wayland compositor";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    flake-utils.url = "github:numtide/flake-utils";

    pywm.url = "github:jbuchermn/pywm/v0.3";
    pywm.inputs.nixpkgs.follows = "nixpkgs";

    dasbus.url = "path:dist/nixos/dasbus";
    dasbus.inputs.nixpkgs.follows = "nixpkgs";
    dasbus.inputs.flake-utils.follows = "flake-utils";
  };

  outputs = { self, nixpkgs, pywm, flake-utils, dasbus }:
  flake-utils.lib.eachDefaultSystem (
    system:
    let
      pkgs = nixpkgs.legacyPackages.${system}; 
      pywmpkg = pywm.packages.${system};
      dasbuspkg = dasbus.packages.${system};
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
            dasbuspkg.dasbus1
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
