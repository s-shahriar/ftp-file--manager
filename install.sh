#!/bin/bash
# FTP File Manager - Installation Script

set -e

echo "========================================"
echo "  FTP File Manager - Installation"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Linux
if [[ "$(uname)" != "Linux" ]]; then
    echo -e "${RED}Error: This tool only supports Linux${NC}"
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.6 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION detected"

# Make scripts executable
echo ""
echo "Making scripts executable..."
chmod +x ftptool.py ftpsend.py ftpsend-gui
echo -e "${GREEN}✓${NC} Scripts are now executable"

# Create ~/bin directory
echo ""
echo "Setting up ~/bin directory..."
mkdir -p ~/bin
echo -e "${GREEN}✓${NC} ~/bin directory created"

# Copy executables
echo ""
echo "Installing executables to ~/bin..."
cp ftptool.py ~/bin/ftptool
cp ftpsend.py ~/bin/ftpsend
cp ftpsend-gui ~/bin/ftpsend-gui
echo -e "${GREEN}✓${NC} Executables installed"

# Add to PATH if not already there
if ! grep -q 'export PATH="$HOME/bin:$PATH"' ~/.bashrc; then
    echo ""
    echo "Adding ~/bin to PATH in ~/.bashrc..."
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    echo -e "${GREEN}✓${NC} PATH updated in ~/.bashrc"
else
    echo ""
    echo -e "${YELLOW}Note:${NC} ~/bin already in PATH"
fi

# Ask about Dolphin integration
echo ""
read -p "Do you want to install Dolphin right-click integration? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if konsole is installed
    if ! command -v konsole &> /dev/null; then
        echo -e "${YELLOW}Warning: konsole is not installed. Dolphin integration requires konsole.${NC}"
        echo "Install it with: sudo apt install konsole"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Skipping Dolphin integration."
        else
            # Install service menu
            mkdir -p ~/.local/share/kio/servicemenus
            cp ftpsend.desktop ~/.local/share/kio/servicemenus/
            sed -i "s/YOUR_USERNAME/$USER/g" ~/.local/share/kio/servicemenus/ftpsend.desktop
            echo -e "${GREEN}✓${NC} Dolphin service menu installed"

            # Restart Dolphin
            if pgrep -x "dolphin" > /dev/null; then
                echo "Restarting Dolphin..."
                killall dolphin 2>/dev/null || true
                sleep 1
            fi
        fi
    else
        # Install service menu
        mkdir -p ~/.local/share/kio/servicemenus
        cp ftpsend.desktop ~/.local/share/kio/servicemenus/
        sed -i "s/YOUR_USERNAME/$USER/g" ~/.local/share/kio/servicemenus/ftpsend.desktop
        echo -e "${GREEN}✓${NC} Dolphin service menu installed"

        # Restart Dolphin
        if pgrep -x "dolphin" > /dev/null; then
            echo "Restarting Dolphin..."
            killall dolphin 2>/dev/null || true
            sleep 1
        fi
    fi
fi

echo ""
echo "========================================"
echo -e "${GREEN}  Installation Complete!${NC}"
echo "========================================"
echo ""
echo "To start using the tools:"
echo "  1. Restart your terminal or run: source ~/.bashrc"
echo "  2. Run 'ftptool' to open the interactive file manager"
echo "  3. Run 'ftpsend file.txt' to quickly send a file"
echo ""
echo "Configuration:"
echo "  - Edit default server in ftptool.py (lines 16-20)"
echo "  - Edit default server in ftpsend.py (lines 23-26)"
echo "  - Edit default server in ftpsend-gui (lines 5-6)"
echo ""
echo "Or just connect once and the tools will remember your server!"
echo ""
echo "For more info, see: README.md"
echo ""
