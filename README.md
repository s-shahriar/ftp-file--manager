# FTP File Manager

A terminal-based FTP file manager with a beautiful TUI (Text User Interface) for easy file transfers between your computer and FTP servers.

![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)

## Features

- **Interactive TUI** - Navigate with arrow keys like a modern file manager (ranger/mc style)
- **Dual-pane concept** - Switch between local and remote views with Tab
- **Background transfers** - Non-blocking uploads/downloads with real-time progress bar
- **Transfer speed display** - Monitor upload/download speeds in real-time
- **Full CRUD operations** - Create, Rename, Delete files and folders on both local and remote
- **View & Edit** - View file contents or edit remote files directly
- **Color-coded interface** - Blue theme for remote, Cyan for local - never confuse which side you're on!
- **Confirmation modals** - Color-coded modals (red for delete, cyan for upload, green for download)
- **Recursive operations** - Upload/download/delete entire folders
- **Dolphin integration** - Right-click "Send to FTP" option for KDE users

## Requirements

- **Python 3.6+** (uses only standard library - no pip install needed!)
- **Linux** (tested on Ubuntu/Debian)
- **FTP Server** running on target device (e.g., phone with FTP server app)

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/s-shahriar/ftp-file--manager.git
cd ftp-file--manager
```

### Step 2: Make Scripts Executable

```bash
chmod +x ftptool.py ftpsend.py
```

### Step 3: Configure Your FTP Server

Edit the default server settings in both files:

**ftptool.py** (line 16-20):
```python
DEFAULT_HOST = "192.168.1.100"  # Your FTP server IP
DEFAULT_PORT = 2121             # Your FTP server port
DEFAULT_USER = "anonymous"      # Username (if required)
DEFAULT_PASS = ""               # Password (if required)
```

**ftpsend.py** (line 12-16):
```python
HOST = "192.168.1.100"  # Your FTP server IP
PORT = 2121             # Your FTP server port
USER = "anonymous"
PASS = ""
```

### Step 4 (Optional): Add to System PATH

To run from anywhere:

```bash
mkdir -p ~/bin
cp ftptool.py ~/bin/ftptool
cp ftpsend.py ~/bin/ftpsend

# Add to PATH (add this line to ~/.bashrc)
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Step 5 (Optional): Dolphin Right-Click Integration (KDE)

To add "Send to FTP Server" option in Dolphin file manager:

```bash
# Create service menu directory
mkdir -p ~/.local/share/kio/servicemenus

# Copy the desktop file
cp ftpsend.desktop ~/.local/share/kio/servicemenus/

# Edit to set correct path
nano ~/.local/share/kio/servicemenus/ftpsend.desktop
# Change: Exec=/path/to/ftpsend.py %F
# To:     Exec=/home/YOUR_USERNAME/bin/ftpsend %F
```

Restart Dolphin or log out/in to see the new option.

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
1. Press `c` to connect to the FTP server
2. Use `Tab` to switch between LOCAL and REMOTE views
3. Navigate with arrow keys, Enter to open folders
4. In LOCAL view: press `u` to upload selected file
5. In REMOTE view: press `d` to download selected file

### Quick Send (ftpsend)

For quick uploads without the TUI:

```bash
# Send single file
./ftpsend.py document.pdf

# Send multiple files
./ftpsend.py file1.pdf file2.jpg file3.zip

# Send entire folder (recursive)
./ftpsend.py ~/Documents/project/
```

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
| `c` | Connect/Disconnect | Both |
| `s` | Set server address | Disconnected |
| `u` | Upload file | LOCAL view |
| `d` | Download file | REMOTE view |
| `D` | Delete (with confirmation) | Both |
| `r` | Rename | Both |
| `m` | Create directory | Both |
| `v` | View file content | REMOTE view |
| `e` | Edit file | REMOTE view |
| `R` | Refresh listing | Both |
| `x` | Cancel ongoing transfer | During transfer |
| `q` | Quit | Both |

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
chmod +x ftptool.py ftpsend.py
```

### Colors not showing properly
- Make sure your terminal supports 256 colors
- Try a different terminal emulator (e.g., Konsole, GNOME Terminal)

## License

MIT License - feel free to use, modify, and distribute.

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

