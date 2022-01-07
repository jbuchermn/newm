{
  description = "newm - Wayland compositor";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pywm.url = "github:jbuchermn/pywm/0cca4a8";
    pywm.inputs.nixpkgs.follows = "nixpkgs";
  };

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
          version = "0.3alpha";

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

      devShell = let
        my-python = pkgs.python3;
        python-with-my-packages = my-python.withPackages (ps: with ps; [
          pywmpkg.pywm
          pycairo
          psutil
          websockets
          python-pam
          pyfiglet
          fuzzywuzzy

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
