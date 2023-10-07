{ pkgs ? import <nixpkgs> {} }:
  pkgs.mkShell {
    # nativeBuildInputs is usually what you want -- tools you need to run
    nativeBuildInputs = with pkgs.buildPackages; [
    	python311
	python311Packages.discordpy
	python311Packages.psycopg2
	python311Packages.numpy
	postgresql
    ];
}
