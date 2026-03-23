#!/bin/bash
# stegx - Remote Silent Installer

echo "[*] Installing stegx Suite..."

# 1. Create a hidden directory for the tool
INSTALL_DIR="$HOME/.stegx-tool"
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# 2. Silently clone the repo into that hidden folder
git clone --quiet https://github.com/roodra-afk/stegx.git "$INSTALL_DIR"

# 3. Install Python dependencies (Kali/Debian Safe)
python3 -m pip install Pillow cryptography reedsolo rich numpy flit --break-system-packages --user --quiet

# 4. Create the global shortcut
mkdir -p ~/.local/bin
ln -sf "$INSTALL_DIR/stegx/cli.py" ~/.local/bin/stegx
chmod +x "$INSTALL_DIR/stegx/cli.py"

echo "------------------------------------------------"
echo "[+] SUCCESS: stegx is now a global command."
echo "[+] Usage: Type 'stegx --help' to start."
echo "------------------------------------------------"
