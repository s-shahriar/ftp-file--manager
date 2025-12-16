#!/bin/bash
# FTP File Manager - Uninstallation Script

set -e

echo "========================================"
echo "  FTP File Manager - Uninstallation"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}WARNING: This will remove all FTP File Manager components${NC}"
echo ""
read -p "Are you sure you want to uninstall? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo "Removing executables from ~/bin..."
if [ -f ~/bin/ftptool ]; then
    rm -f ~/bin/ftptool
    echo -e "${GREEN}✓${NC} Removed ftptool"
fi

if [ -f ~/bin/ftpsend ]; then
    rm -f ~/bin/ftpsend
    echo -e "${GREEN}✓${NC} Removed ftpsend"
fi

if [ -f ~/bin/ftpsend-gui ]; then
    rm -f ~/bin/ftpsend-gui
    echo -e "${GREEN}✓${NC} Removed ftpsend-gui"
fi

# Remove Dolphin integration
echo ""
echo "Removing Dolphin integration..."
if [ -f ~/.local/share/kio/servicemenus/ftpsend.desktop ]; then
    rm -f ~/.local/share/kio/servicemenus/ftpsend.desktop
    echo -e "${GREEN}✓${NC} Removed Dolphin service menu"
fi

# Remove configuration
echo ""
read -p "Remove saved connection settings (~/.ftpsend_config.json)? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f ~/.ftpsend_config.json ]; then
        rm -f ~/.ftpsend_config.json
        echo -e "${GREEN}✓${NC} Removed configuration file"
    fi
else
    echo -e "${YELLOW}Note:${NC} Keeping configuration file"
fi

# Remove PATH line
echo ""
read -p "Remove ~/bin from PATH in ~/.bashrc? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if grep -q 'export PATH="$HOME/bin:$PATH"' ~/.bashrc; then
        sed -i '/export PATH="\$HOME\/bin:\$PATH"/d' ~/.bashrc
        echo -e "${GREEN}✓${NC} Removed PATH line from ~/.bashrc"
        echo -e "${YELLOW}Note:${NC} Run 'source ~/.bashrc' to apply changes"
    fi
else
    echo -e "${YELLOW}Note:${NC} Keeping ~/bin in PATH"
fi

# Restart Dolphin
if pgrep -x "dolphin" > /dev/null; then
    echo ""
    echo "Restarting Dolphin..."
    killall dolphin 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓${NC} Dolphin restarted"
fi

# Ask about removing repository
echo ""
read -p "Remove the project directory ($(pwd))? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    PROJECT_DIR=$(pwd)
    cd ~
    rm -rf "$PROJECT_DIR"
    echo -e "${GREEN}✓${NC} Removed project directory"
fi

echo ""
echo "========================================"
echo -e "${GREEN}  Uninstallation Complete!${NC}"
echo "========================================"
echo ""
echo "Verifying removal..."
if ! command -v ftptool &> /dev/null && ! command -v ftpsend &> /dev/null; then
    echo -e "${GREEN}✓${NC} All tools successfully removed"
else
    echo -e "${YELLOW}Note:${NC} Some tools may still be in PATH from terminal cache"
    echo "Please restart your terminal or run: hash -r"
fi
echo ""
