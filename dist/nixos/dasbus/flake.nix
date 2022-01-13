{
  description = "dasbus";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
  flake-utils.lib.eachDefaultSystem (
    system:
    let
      pkgs = nixpkgs.legacyPackages.${system}; 
    in
    {
      packages.dasbus = pkgs.python3.pkgs.buildPythonPackage rec {
        pname = "dasbus";
        version = "1.6";

        src = pkgs.python3.pkgs.fetchPypi {
          inherit pname version;
          sha256 = "sha256-FJrY/Iw9KYMhq1AVm1R6soNImaieR+IcbULyyS5W6U0=";
        };

        setuptoolsCheckPhase = "true";

        propagatedBuildInputs = with pkgs.python3Packages; [ pygobject3 ];
      };
    }
  );
}
