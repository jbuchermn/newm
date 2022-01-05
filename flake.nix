{
  description = "newm - Wayland compositor";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.pywm.url = "path:/home/jonas/pywmv2";

  outputs = { self, nixpkgs, pywm, flake-utils }:
  flake-utils.lib.eachDefaultSystem (
    system:
    let
      pkgs = nixpkgs.legacyPackages.${system}; 
      pywmpkg = pywm.packages.${system};
    in
    {
      devShell = import ./dev/nix/shell.nix { inherit pkgs; pywm = pywmpkg.pywm; };
      packages.newm = import ./dev/nix/newm.nix { inherit pkgs; pywm = pywmpkg.pywm; };
    }
  );
}
