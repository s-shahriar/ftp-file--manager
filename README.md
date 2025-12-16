# FTP File Manager

A terminal-based FTP file manager with a beautiful TUI (Text User Interface) for easy file transfers between your computer and FTP servers.

![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)

## Features

- **Interactive TUI** - Navigate with arrow keys like a modern file manager (ranger/mc style)
- **Dual-pane concept** - Switch between local and remote views with Tab
- **Multiple file selection** - Mark multiple files with spacebar and transfer them in a queue
- **Queue system** - Transfer multiple files sequentially with queue progress display
- **Background transfers** - Non-blocking uploads/downloads with real-time progress bar
- **Transfer speed display** - Monitor upload/download speeds in real-time
- **Auto-reconnect** - Remembers last successful connection IP/port
- **Full CRUD operations** - Create, Rename, Delete files and folders on both local and remote
- **View & Edit** - View file contents or edit remote files directly
- **Color-coded interface** - Blue theme for remote, Cyan for local - never confuse which side you're on!
- **Confirmation modals** - Color-coded modals (red for delete, cyan for upload, green for download)
- **Recursive operations** - Upload/download/delete entire folders
- **Cancel transfers** - Press Ctrl+C to cancel ongoing transfers
- **Dolphin integration** - Right-click "Send to FTP" option for KDE users with prefilled IP editing

## Requirements

- **Python 3.6+** (uses only standard library - no pip install needed!)
- **Linux** (tested on Ubuntu/Debian/KDE Neon)
- **Konsole** (KDE terminal - for Dolphin integration, optional)
- **FTP Server** running on target device (e.g., phone with FTP server app)

## Installation

### Quick Install (Recommended)

```bash
git clone https://github.com/s-shahriar/ftp-file--manager.git
cd ftp-file--manager
./install.sh
```

The install script will:
- Make all scripts executable
- Copy tools to ~/bin
- Add ~/bin to your PATH
- Optionally install Dolphin integration
- Check for dependencies (Python 3.6+, konsole)

**Then restart your terminal or run:** `source ~/.bashrc`

---

### Manual Installation

If you prefer to install manually, follow these steps:

### Step 1: Clone the Repository

```bash
git clone https://github.com/s-shahriar/ftp-file--manager.git
cd ftp-file--manager
```

### Step 2: Make Scripts Executable

```bash
chmod +x ftptool.py ftpsend.py ftpsend-gui
```

### Step 3: Configure Your FTP Server

Edit the default server settings in the configuration files:

**ftptool.py** (around line 16-20):
```python
DEFAULT_HOST = "192.168.0.103"  # Your FTP server IP
DEFAULT_PORT = 9999             # Your FTP server port
DEFAULT_USER = "anonymous"      # Username (if required)
DEFAULT_PASS = ""               # Password (if required)
```

**ftpsend.py** (around line 23-26):
```python
DEFAULT_HOST = "192.168.0.103"  # Your FTP server IP
DEFAULT_PORT = 9999             # Your FTP server port
USER = "anonymous"
PASS = ""
```

**ftpsend-gui** (line 5-6):
```bash
DEFAULT_HOST="192.168.0.103"
DEFAULT_PORT="9999"
```

**Note:** The tools remember your last successful connection, so you only need to set this once. After the first successful connection, they'll automatically use the last working IP:port.

### Step 4: Add to System PATH

To run from anywhere (required for Dolphin integration):

```bash
# Create bin directory if it doesn't exist
mkdir -p ~/bin

# Copy executables (without .py extension for cleaner commands)
cp ftptool.py ~/bin/ftptool
cp ftpsend.py ~/bin/ftpsend
cp ftpsend-gui ~/bin/ftpsend-gui

# Add to PATH if not already there
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
which ftptool ftpsend ftpsend-gui
```

### Step 5 (Optional): Dolphin Right-Click Integration (KDE)

To add "Send to FTP Server" option in Dolphin file manager:

```bash
# Create service menu directory
mkdir -p ~/.local/share/kio/servicemenus

# Copy the desktop file
cp ftpsend.desktop ~/.local/share/kio/servicemenus/

# Edit to set your username
sed -i "s/YOUR_USERNAME/$USER/g" ~/.local/share/kio/servicemenus/ftpsend.desktop

# Restart Dolphin
killall dolphin 2>/dev/null
```

**What this does:**
- Adds a right-click menu option "Send to FTP Server" in Dolphin
- Works with single or multiple file selection
- Opens a terminal with options to send or change server address
- IP address is prefilled and editable (use arrow keys to edit just the last part)
- Files are transferred sequentially with queue progress display

To test: Right-click any file(s) in Dolphin → "Send to FTP Server"

## Usage

### Interactive File Manager (ftptool)

```bash
# Run from the cloned directory
./ftptool.py

# Or if added to PATH
ftptool

# Connect to specific server directly
ftptool ftp://192.168.1.100:2121/
```

**Workflow:**
1. Connects automatically to last successful server (or default on first run)
2. If connection fails, press `s` to change server address
3. Use `Tab` to switch between LOCAL and REMOTE views
4. Navigate with arrow keys, Enter to open folders
5. Press `Space` to mark multiple files (shows ✓ checkmark)
6. In LOCAL view: press `u` to upload selected/marked file(s)
7. In REMOTE view: press `d` to download selected/marked file(s)
8. Multiple files transfer sequentially with queue progress display

**Smart Connection Memory:**
- Tools remember the last successful IP:port
- Next time you run, it automatically uses the last working server
- No need to edit config files when your phone's IP changes!

### Quick Send (ftpsend)

For quick uploads without the TUI:

```bash
# Send single file
./ftpsend.py document.pdf

# Send multiple files (queued sequentially)
./ftpsend.py file1.pdf file2.jpg file3.zip

# Send entire folder (recursive)
./ftpsend.py ~/Documents/project/

# Mix files and folders
./ftpsend.py document.pdf ~/Photos/ report.docx
```

**Features:**
- Shows styled progress bars with transfer speed
- Multiple files are transferred sequentially with queue display: `[2/5] filename.txt`
- Press `Ctrl+C` to cancel transfer (auto-closes terminal)
- If connection fails, choose to retry or change server
- Remembers last successful connection

**Dolphin Integration:**
- Right-click single or multiple file(s) → "Send to FTP Server"
- Option to change IP before sending with prefilled current IP
- Use arrow keys to edit just the part of IP you need to change
- Just press Enter to use last successful connection
- Files transfer sequentially with queue progress

## Keyboard Shortcuts

### Navigation
| Key | Action |
|-----|--------|
| `↑` / `k` | Move up |
| `↓` / `j` | Move down |
| `Enter` / `→` / `l` | Open directory |
| `←` / `h` / `Backspace` | Go to parent directory |
| `PgUp` / `PgDn` | Scroll page up/down |
| `Home` / `End` | Jump to first/last item |
| `Tab` | Switch between Remote/Local view |

### File Operations
| Key | Action | Available In |
|-----|--------|--------------|
| `Space` | Mark/unmark file for batch operations | Both |
| `c` | Connect/Disconnect | Both |
| `s` | Set server address | Disconnected |
| `u` | Upload file/marked files | LOCAL view |
| `d` | Download file/marked files | REMOTE view |
| `D` | Delete (with confirmation) | Both |
| `r` | Rename | Both |
| `m` | Create directory | Both |
| `v` | View file content | REMOTE view |
| `e` | Edit file | REMOTE view |
| `R` | Refresh listing | Both |
| `x` | Cancel ongoing transfer | During transfer |
| `q` | Quit | Both |

**Batch Operations:**
- Press `Space` to mark files (shows ✓ checkmark)
- Mark multiple files on either LOCAL or REMOTE side
- Press `u` (upload) or `d` (download) to transfer all marked files
- Files are transferred sequentially with queue progress: `[2/5] filename.txt`
- Marked files are automatically cleared after transfer

## Color Scheme

| Element | Color | Meaning |
|---------|-------|---------|
| REMOTE view | Blue | You're browsing the FTP server |
| LOCAL view | Cyan/Teal | You're browsing your computer |
| Delete modal | Red | Dangerous action - be careful! |
| Upload modal | Cyan | Sending to server |
| Download modal | Green | Receiving from server |
| Success messages | Green | Operation completed |
| Error messages | Red | Something went wrong |

## Common Use Cases

### Transfer files between phone and laptop
1. Install an FTP server app on your phone (e.g., "WiFi FTP Server")
2. Start the FTP server and note the IP:PORT
3. Configure ftptool with that IP:PORT
4. Run `ftptool` and press `c` to connect
5. Navigate and transfer files!

### Batch upload to server
```bash
# Upload all PDFs in current directory
ftpsend *.pdf

# Upload entire project folder
ftpsend ~/projects/my-website/
```

## Troubleshooting

### "Connection failed" error
- Check if FTP server is running on the target device
- Verify IP address and port are correct
- Ensure both devices are on the same network
- Check firewall settings

### "Permission denied" on scripts
```bash
chmod +x ftptool.py ftpsend.py ftpsend-gui
```

### Colors not showing properly
- Make sure your terminal supports 256 colors
- Try a different terminal emulator (e.g., Konsole, GNOME Terminal)

### Dolphin integration not showing
```bash
# Reinstall the service menu
cp ftpsend.desktop ~/.local/share/kio/servicemenus/
sed -i "s/YOUR_USERNAME/$USER/g" ~/.local/share/kio/servicemenus/ftpsend.desktop
killall dolphin
```

## Uninstallation

### Quick Uninstall (Recommended)

```bash
cd ftp-file--manager
./uninstall.sh
```

The uninstall script will interactively:
- Remove executables from ~/bin
- Remove Dolphin integration
- Ask if you want to remove saved connection settings
- Ask if you want to remove ~/bin from PATH
- Ask if you want to remove the project directory
- Restart Dolphin if needed

---

### Manual Uninstallation

To manually remove FTP File Manager from your system:

```bash
# Remove executables from PATH
rm -f ~/bin/ftptool
rm -f ~/bin/ftpsend
rm -f ~/bin/ftpsend-gui

# Remove Dolphin integration
rm -f ~/.local/share/kio/servicemenus/ftpsend.desktop

# Remove configuration file (saved connections)
rm -f ~/.ftpsend_config.json

# Remove the cloned repository
cd ~
rm -rf ~/Projects/ftp-file-manager

# Restart Dolphin if it was running
killall dolphin 2>/dev/null

echo "FTP File Manager has been completely uninstalled."
```

**Optional:** Remove the PATH export line from ~/.bashrc:

```bash
# Remove PATH line from .bashrc
sed -i '/export PATH="\$HOME\/bin:\$PATH"/d' ~/.bashrc
source ~/.bashrc
```

After uninstallation, verify removal:
```bash
which ftptool ftpsend ftpsend-gui  # Should return nothing
```

## License

MIT License - feel free to use, modify, and distribute.

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

