with import <nixpkgs> {};
pkgs.mkShell {
  buildInputs = [ python311 ];
  shellHook = ''
    if [ ! -d venv ]; then
      python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt --quiet 2>/dev/null
  '';
}
