#!/usr/bin/env python3
"""
FTP Tool - Interactive FTP file manager with keyboard navigation
"""

import os
import sys
import curses
import ftplib
import tempfile
import subprocess
import threading
import time
import json
from pathlib import Path

# Config file to remember last successful connection
CONFIG_FILE = Path.home() / ".ftptool_config.json"

# Default FTP settings
DEFAULT_HOST = "192.168.0.103"
DEFAULT_PORT = 9999
DEFAULT_USER = "anonymous"
DEFAULT_PASS = ""

# Load last successful connection or use defaults
def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('host', DEFAULT_HOST), config.get('port', DEFAULT_PORT)
        except:
            pass
    return DEFAULT_HOST, DEFAULT_PORT

def save_config(host, port):
    """Save last successful connection"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'host': host, 'port': port}, f)
    except:
        pass

class FTPManager:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.ftp = None
        self.connected = False
        # Load last successful connection
        self.host, self.port = load_config()
        self.local_dir = Path.home() / "Downloads"  # Start in Downloads
        self.remote_dir = "/"
        self.remote_files = []
        self.local_files = []
        self.cursor = 0
        self.scroll_offset = 0
        self.mode = "remote"  # "remote" or "local"
        self.message = ""
        self.message_type = "info"  # "info", "success", "error"

        # Background transfer state
        self.transfer_active = False
        self.transfer_progress = 0
        self.transfer_total = 0
        self.transfer_filename = ""
        self.transfer_action = ""
        self.transfer_cancelled = False
        self.transfer_thread = None
        self.transfer_start_time = 0
        self.transfer_last_progress = 0
        self.transfer_last_time = 0
        self.transfer_speed = 0

        # Initialize curses
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)      # Info messages
        curses.init_pair(2, curses.COLOR_GREEN, -1)     # Success/Connected
        curses.init_pair(3, curses.COLOR_RED, -1)       # Error/Disconnected
        curses.init_pair(4, curses.COLOR_YELLOW, -1)    # Warning/Help bar
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_CYAN)   # Header bar

        # Remote theme (Sky Blue/Cyan)
        curses.init_pair(6, curses.COLOR_BLUE, -1)      # Remote path bar
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Selected (remote)
        curses.init_pair(8, curses.COLOR_BLUE, -1)      # Remote directories

        # Local theme (Teal/Cyan-Green)
        curses.init_pair(9, curses.COLOR_CYAN, -1)      # Local path bar
        curses.init_pair(10, curses.COLOR_WHITE, curses.COLOR_CYAN)  # Selected (local) - white text for visibility
        curses.init_pair(11, curses.COLOR_CYAN, -1)     # Local directories

        # Modal colors
        curses.init_pair(12, curses.COLOR_RED, -1)      # Delete modal (danger)
        curses.init_pair(13, curses.COLOR_CYAN, -1)     # Upload modal
        curses.init_pair(14, curses.COLOR_GREEN, -1)    # Download modal

        curses.curs_set(0)  # Hide cursor
        self.stdscr.keypad(True)

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:>7.1f} {unit}"
            size /= 1024
        return f"{size:>7.1f} TB"

    def set_message(self, msg, msg_type="info"):
        self.message = msg
        self.message_type = msg_type

    def parse_list_line(self, line):
        parts = line.split(None, 8)
        if len(parts) >= 9:
            return {
                'name': parts[8],
                'size': int(parts[4]) if parts[4].isdigit() else 0,
                'is_dir': parts[0].startswith('d'),
                'perms': parts[0],
            }
        return None

    def refresh_remote(self):
        if not self.connected:
            self.remote_files = []
            return
        try:
            self.remote_files = [{'name': '..', 'is_dir': True, 'size': 0, 'perms': ''}]
            items = []
            self.ftp.retrlines('LIST', items.append)
            for item in items:
                parsed = self.parse_list_line(item)
                if parsed:
                    self.remote_files.append(parsed)
            # Sort: directories first
            self.remote_files[1:] = sorted(self.remote_files[1:],
                key=lambda x: (not x['is_dir'], x['name'].lower()))
            self.remote_dir = self.ftp.pwd()
        except Exception as e:
            self.set_message(f"Error: {e}", "error")

    def refresh_local(self):
        try:
            self.local_files = [{'name': '..', 'is_dir': True, 'size': 0, 'path': self.local_dir.parent}]
            items = sorted(self.local_dir.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            for item in items:
                self.local_files.append({
                    'name': item.name,
                    'is_dir': item.is_dir(),
                    'size': item.stat().st_size if item.is_file() else 0,
                    'path': item
                })
        except PermissionError:
            self.set_message("Permission denied", "error")

    def get_current_list(self):
        return self.remote_files if self.mode == "remote" else self.local_files

    def get_selected_item(self):
        items = self.get_current_list()
        if 0 <= self.cursor < len(items):
            return items[self.cursor]
        return None

    def connect(self):
        try:
            self.set_message(f"Connecting to {self.host}:{self.port}...", "info")
            self.draw()
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.host, self.port, timeout=10)
            self.ftp.login(DEFAULT_USER, DEFAULT_PASS)
            self.connected = True
            # Save successful connection
            save_config(self.host, self.port)
            self.refresh_remote()
            self.cursor = 0
            self.scroll_offset = 0
            self.set_message("Connected!", "success")
        except Exception as e:
            self.set_message(f"Connection failed: {e}", "error")
            self.connected = False

    def disconnect(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                pass
        self.ftp = None
        self.connected = False
        self.remote_files = []
        self.set_message("Disconnected", "info")

    def enter_directory(self):
        item = self.get_selected_item()
        if not item or not item['is_dir']:
            return

        if self.mode == "remote" and self.connected:
            try:
                if item['name'] == '..':
                    self.ftp.cwd('..')
                else:
                    self.ftp.cwd(item['name'])
                self.refresh_remote()
                self.cursor = 0
                self.scroll_offset = 0
            except Exception as e:
                self.set_message(f"Error: {e}", "error")
        elif self.mode == "local":
            if item['name'] == '..':
                self.local_dir = self.local_dir.parent
            else:
                self.local_dir = item['path']
            self.refresh_local()
            self.cursor = 0
            self.scroll_offset = 0

    def upload_selected(self):
        if not self.connected:
            self.set_message("Not connected", "error")
            return
        if self.mode != "local":
            self.set_message("Upload only works in LOCAL view. Press 'd' to download.", "info")
            return
        if self.transfer_active:
            self.set_message("Transfer already in progress", "error")
            return

        item = self.get_selected_item()
        if not item or item['name'] == '..':
            return

        if item['is_dir']:
            self.upload_folder_selected()
            return

        # Confirm upload - show target remote folder
        if not self.confirm(f"Upload '{item['name']}' to {self.remote_dir}?", "upload"):
            self.set_message("Upload cancelled", "info")
            return

        filepath = item['path']
        file_size = filepath.stat().st_size
        filename = item['name']

        # Setup transfer state
        self.transfer_active = True
        self.transfer_progress = 0
        self.transfer_total = file_size
        self.transfer_filename = filename
        self.transfer_action = "Uploading"
        self.transfer_cancelled = False
        self.transfer_start_time = time.time()
        self.transfer_last_time = time.time()
        self.transfer_last_progress = 0
        self.transfer_speed = 0

        def do_upload():
            try:
                # Create a new FTP connection for the transfer
                transfer_ftp = ftplib.FTP()
                transfer_ftp.connect(self.host, self.port, timeout=30)
                transfer_ftp.login(DEFAULT_USER, DEFAULT_PASS)
                transfer_ftp.cwd(self.remote_dir)

                def callback(data):
                    if self.transfer_cancelled:
                        raise Exception("Cancelled by user")
                    self.transfer_progress += len(data)

                with open(filepath, 'rb') as f:
                    transfer_ftp.storbinary(f"STOR {filename}", f, blocksize=8192, callback=callback)

                transfer_ftp.quit()
                self.refresh_remote()
                self.set_message(f"Uploaded: {filename} ({self.format_size(file_size).strip()})", "success")
            except Exception as e:
                if "Cancelled" in str(e):
                    self.set_message("Upload cancelled", "info")
                else:
                    self.set_message(f"Upload failed: {e}", "error")
            finally:
                self.transfer_active = False

        self.transfer_thread = threading.Thread(target=do_upload, daemon=True)
        self.transfer_thread.start()

    def upload_folder_selected(self):
        """Upload entire folder recursively"""
        if not self.connected:
            self.set_message("Not connected", "error")
            return
        if self.transfer_active:
            self.set_message("Transfer already in progress", "error")
            return

        item = self.get_selected_item()
        if not item or item['name'] == '..' or not item['is_dir']:
            return

        folder_path = item['path']
        folder_name = item['name']

        # Confirm upload
        if not self.confirm(f"Upload folder '{folder_name}/' to {self.remote_dir}?", "upload"):
            self.set_message("Upload cancelled", "info")
            return

        # Count files
        file_count = sum(1 for _ in folder_path.rglob('*') if _.is_file())

        self.transfer_active = True
        self.transfer_filename = f"{folder_name}/ ({file_count} files)"
        self.transfer_action = "Uploading"
        self.transfer_progress = 0
        self.transfer_total = 1  # We'll update this as we go
        self.transfer_cancelled = False

        def do_folder_upload():
            try:
                transfer_ftp = ftplib.FTP()
                transfer_ftp.connect(self.host, self.port, timeout=30)
                transfer_ftp.login(DEFAULT_USER, DEFAULT_PASS)
                transfer_ftp.cwd(self.remote_dir)

                uploaded_count = [0]

                def upload_recursive(local_path, remote_path=""):
                    if self.transfer_cancelled:
                        raise Exception("Cancelled by user")

                    # Create remote directory
                    if remote_path:
                        try:
                            transfer_ftp.mkd(remote_path)
                        except:
                            pass
                        transfer_ftp.cwd(self.remote_dir + '/' + remote_path if remote_path else self.remote_dir)

                    # Upload files and recurse into subdirectories
                    for item in sorted(local_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                        if self.transfer_cancelled:
                            raise Exception("Cancelled by user")

                        if item.is_file():
                            with open(item, 'rb') as f:
                                transfer_ftp.storbinary(f"STOR {item.name}", f, blocksize=8192)
                            uploaded_count[0] += 1
                            self.transfer_filename = f"{folder_name}/ ({uploaded_count[0]}/{file_count})"
                        elif item.is_dir():
                            new_remote = f"{remote_path}/{item.name}" if remote_path else item.name
                            upload_recursive(item, new_remote)

                upload_recursive(folder_path, folder_name)

                transfer_ftp.quit()
                self.refresh_remote()
                self.set_message(f"Uploaded folder: {folder_name}/ ({uploaded_count[0]} files)", "success")
            except Exception as e:
                if "Cancelled" in str(e):
                    self.set_message("Upload cancelled", "info")
                else:
                    self.set_message(f"Upload failed: {e}", "error")
            finally:
                self.transfer_active = False

        self.transfer_thread = threading.Thread(target=do_folder_upload, daemon=True)
        self.transfer_thread.start()

    def download_selected(self):
        if not self.connected:
            self.set_message("Not connected", "error")
            return
        if self.mode != "remote":
            self.set_message("Download only works in REMOTE view. Press 'u' to upload.", "info")
            return
        if self.transfer_active:
            self.set_message("Transfer already in progress", "error")
            return

        item = self.get_selected_item()
        if not item or item['name'] == '..' or item['is_dir']:
            return

        # Confirm download
        if not self.confirm(f"Download '{item['name']}' to {self.local_dir}?", "download"):
            self.set_message("Download cancelled", "info")
            return

        file_size = item['size']
        filename = item['name']
        local_path = self.local_dir / filename
        remote_dir = self.remote_dir

        # Setup transfer state
        self.transfer_active = True
        self.transfer_progress = 0
        self.transfer_total = file_size
        self.transfer_filename = filename
        self.transfer_action = "Downloading"
        self.transfer_cancelled = False
        self.transfer_start_time = time.time()
        self.transfer_last_time = time.time()
        self.transfer_last_progress = 0
        self.transfer_speed = 0

        def do_download():
            try:
                # Create a new FTP connection for the transfer
                transfer_ftp = ftplib.FTP()
                transfer_ftp.connect(self.host, self.port, timeout=30)
                transfer_ftp.login(DEFAULT_USER, DEFAULT_PASS)
                transfer_ftp.cwd(remote_dir)

                with open(local_path, 'wb') as f:
                    def callback(data):
                        if self.transfer_cancelled:
                            raise Exception("Cancelled by user")
                        self.transfer_progress += len(data)
                        f.write(data)

                    transfer_ftp.retrbinary(f"RETR {filename}", callback, blocksize=8192)

                transfer_ftp.quit()
                self.refresh_local()
                self.set_message(f"Downloaded: {filename} to {self.local_dir}", "success")
            except Exception as e:
                if "Cancelled" in str(e):
                    try:
                        local_path.unlink()
                    except:
                        pass
                    self.set_message("Download cancelled", "info")
                else:
                    self.set_message(f"Download failed: {e}", "error")
            finally:
                self.transfer_active = False

        self.transfer_thread = threading.Thread(target=do_download, daemon=True)
        self.transfer_thread.start()

    def delete_remote_dir_recursive(self, dirname):
        """Recursively delete a remote directory"""
        # Save current directory
        original_dir = self.ftp.pwd()

        try:
            self.ftp.cwd(dirname)

            # Get listing
            items = []
            self.ftp.retrlines('LIST', items.append)

            for item in items:
                parsed = self.parse_list_line(item)
                if parsed:
                    if parsed['is_dir']:
                        self.delete_remote_dir_recursive(parsed['name'])
                    else:
                        self.ftp.delete(parsed['name'])

            # Go back and remove the now-empty directory
            self.ftp.cwd(original_dir)
            self.ftp.rmd(dirname)
        except Exception as e:
            self.ftp.cwd(original_dir)
            raise e

    def delete_selected(self):
        if self.mode == "remote" and self.connected:
            item = self.get_selected_item()
            if not item or item['name'] == '..':
                return

            try:
                if item['is_dir']:
                    self.set_message(f"Deleting {item['name']}...", "info")
                    self.draw()
                    self.delete_remote_dir_recursive(item['name'])
                else:
                    self.ftp.delete(item['name'])
                self.refresh_remote()
                if self.cursor >= len(self.remote_files):
                    self.cursor = max(0, len(self.remote_files) - 1)
                self.set_message(f"Deleted: {item['name']}", "success")
            except Exception as e:
                self.set_message(f"Delete failed: {e}", "error")
        elif self.mode == "local":
            item = self.get_selected_item()
            if not item or item['name'] == '..':
                return
            try:
                path = item['path']
                if path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                else:
                    path.unlink()
                self.refresh_local()
                if self.cursor >= len(self.local_files):
                    self.cursor = max(0, len(self.local_files) - 1)
                self.set_message(f"Deleted: {item['name']}", "success")
            except Exception as e:
                self.set_message(f"Delete failed: {e}", "error")

    def rename_selected(self):
        item = self.get_selected_item()
        if not item or item['name'] == '..':
            return

        new_name = self.get_input("Rename to: ", item['name'])
        if not new_name:
            self.set_message("Rename cancelled", "info")
            return

        if new_name == item['name']:
            return

        if self.mode == "remote" and self.connected:
            try:
                self.ftp.rename(item['name'], new_name)
                self.refresh_remote()
                self.set_message(f"Renamed to: {new_name}", "success")
            except Exception as e:
                self.set_message(f"Rename failed: {e}", "error")
        elif self.mode == "local":
            try:
                old_path = item['path']
                new_path = old_path.parent / new_name
                old_path.rename(new_path)
                self.refresh_local()
                self.set_message(f"Renamed to: {new_name}", "success")
            except Exception as e:
                self.set_message(f"Rename failed: {e}", "error")

    def make_directory(self):
        name = self.get_input("New directory name: ")
        if not name:
            return

        if self.mode == "remote" and self.connected:
            try:
                self.ftp.mkd(name)
                self.refresh_remote()
                self.set_message(f"Created: {name}/", "success")
            except Exception as e:
                self.set_message(f"Failed: {e}", "error")
        elif self.mode == "local":
            try:
                (self.local_dir / name).mkdir()
                self.refresh_local()
                self.set_message(f"Created: {name}/", "success")
            except Exception as e:
                self.set_message(f"Failed: {e}", "error")

    def view_file(self):
        if self.mode != "remote" or not self.connected:
            return

        item = self.get_selected_item()
        if not item or item['is_dir'] or item['name'] == '..':
            return

        try:
            content = []
            self.ftp.retrlines(f"RETR {item['name']}", content.append)
            self.show_file_content(item['name'], content)
        except Exception as e:
            self.set_message(f"Cannot view (binary?): {e}", "error")

    def edit_file(self):
        if self.mode != "remote" or not self.connected:
            return

        item = self.get_selected_item()
        if not item or item['is_dir'] or item['name'] == '..':
            return

        try:
            with tempfile.NamedTemporaryFile(mode='wb', suffix=f'_{item["name"]}', delete=False) as tmp:
                tmp_path = tmp.name
                self.ftp.retrbinary(f"RETR {item['name']}", tmp.write)

            before_mtime = os.path.getmtime(tmp_path)

            curses.endwin()
            editor = os.environ.get('EDITOR', 'nano')
            subprocess.run([editor, tmp_path])
            self.stdscr = curses.initscr()
            curses.start_color()
            curses.curs_set(0)
            self.stdscr.keypad(True)

            after_mtime = os.path.getmtime(tmp_path)
            if after_mtime > before_mtime:
                with open(tmp_path, 'rb') as f:
                    self.ftp.storbinary(f"STOR {item['name']}", f)
                self.set_message(f"Changes saved to {item['name']}", "success")
            else:
                self.set_message("No changes made", "info")

            os.unlink(tmp_path)
            self.refresh_remote()
        except Exception as e:
            self.set_message(f"Edit failed: {e}", "error")

    def get_input(self, prompt, prefill=""):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(h-1, 0, prompt + " " * (w - len(prompt) - 1), curses.color_pair(5))

        # If prefill provided, show it and allow editing
        if prefill:
            self.stdscr.addstr(h-1, len(prompt), prefill)

        self.stdscr.move(h-1, len(prompt) + len(prefill))
        curses.echo()
        curses.curs_set(1)

        if prefill:
            # Use a simple edit approach - show prefill and let user edit from end
            # For better UX, we manually handle input with prefill
            curses.noecho()
            edit_buffer = list(prefill)
            cursor_pos = len(edit_buffer)

            while True:
                # Display current buffer
                display = prompt + "".join(edit_buffer)
                self.stdscr.addnstr(h-1, 0, display.ljust(w-1), w-1, curses.color_pair(5))
                self.stdscr.move(h-1, len(prompt) + cursor_pos)
                self.stdscr.refresh()

                key = self.stdscr.getch()

                if key in (curses.KEY_ENTER, 10, 13):  # Enter
                    break
                elif key == 27:  # Escape - cancel
                    edit_buffer = []
                    break
                elif key in (curses.KEY_BACKSPACE, 127, 8):  # Backspace
                    if cursor_pos > 0:
                        edit_buffer.pop(cursor_pos - 1)
                        cursor_pos -= 1
                elif key == curses.KEY_DC:  # Delete
                    if cursor_pos < len(edit_buffer):
                        edit_buffer.pop(cursor_pos)
                elif key == curses.KEY_LEFT:
                    if cursor_pos > 0:
                        cursor_pos -= 1
                elif key == curses.KEY_RIGHT:
                    if cursor_pos < len(edit_buffer):
                        cursor_pos += 1
                elif key == curses.KEY_HOME:
                    cursor_pos = 0
                elif key == curses.KEY_END:
                    cursor_pos = len(edit_buffer)
                elif 32 <= key <= 126:  # Printable characters
                    edit_buffer.insert(cursor_pos, chr(key))
                    cursor_pos += 1

            result = "".join(edit_buffer).strip()
        else:
            try:
                result = self.stdscr.getstr(h-1, len(prompt), w - len(prompt) - 2).decode('utf-8').strip()
            except:
                result = ""

        curses.noecho()
        curses.curs_set(0)
        return result

    def show_file_content(self, filename, lines):
        scroll = 0
        while True:
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()

            # Header
            header = f" Viewing: {filename} (q to close, ↑↓ to scroll) "
            self.stdscr.addstr(0, 0, header.center(w), curses.color_pair(5))

            # Content
            visible_lines = h - 2
            for i, line in enumerate(lines[scroll:scroll + visible_lines]):
                if i + 1 < h - 1:
                    self.stdscr.addnstr(i + 1, 0, line, w - 1)

            # Footer
            footer = f" Line {scroll + 1}-{min(scroll + visible_lines, len(lines))}/{len(lines)} "
            self.stdscr.addstr(h-1, 0, footer.ljust(w), curses.color_pair(5))

            self.stdscr.refresh()
            key = self.stdscr.getch()

            if key in (ord('q'), ord('Q'), 27):
                break
            elif key == curses.KEY_UP and scroll > 0:
                scroll -= 1
            elif key == curses.KEY_DOWN and scroll < len(lines) - visible_lines:
                scroll += 1
            elif key == curses.KEY_PPAGE:
                scroll = max(0, scroll - visible_lines)
            elif key == curses.KEY_NPAGE:
                scroll = min(len(lines) - visible_lines, scroll + visible_lines)

    def set_server(self):
        # Prefill with current IP for easy editing (just change last octet)
        new_host = self.get_input("Server IP: ", self.host)
        if new_host:
            self.host = new_host

        # Only ask for port if user wants to change it
        new_port = self.get_input("Port: ", str(self.port))
        if new_port:
            try:
                self.port = int(new_port)
            except ValueError:
                pass
        self.set_message(f"Server set to {self.host}:{self.port}", "info")

    def draw(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()

        # Header
        title = "═══ FTP File Manager ═══"
        if self.connected:
            status = f" ● {self.host}:{self.port} "
            status_color = curses.color_pair(2) | curses.A_BOLD
        else:
            status = " ○ Disconnected "
            status_color = curses.color_pair(3) | curses.A_BOLD

        try:
            self.stdscr.addnstr(0, 0, " " * w, w-1, curses.color_pair(5))
            self.stdscr.addstr(0, (w - len(title)) // 2, title, curses.color_pair(5) | curses.A_BOLD)
            self.stdscr.addstr(0, min(w - len(status) - 1, w-len(status)), status[:w-1], status_color)
        except curses.error:
            pass

        # Path bar - different colors for remote vs local
        if self.mode == "remote":
            path_str = f" 🌐 REMOTE: {self.remote_dir} "
            path_color = curses.color_pair(6)  # Magenta for remote
        else:
            path_str = f" 💻 LOCAL: {self.local_dir} "
            path_color = curses.color_pair(9)  # Green for local
        mode_indicator = "[TAB to switch]"

        try:
            self.stdscr.addnstr(1, 0, " " * w, w-1, path_color)
            self.stdscr.addnstr(1, 0, path_str, w - len(mode_indicator) - 2, path_color | curses.A_BOLD)
            self.stdscr.addnstr(1, w - len(mode_indicator) - 1, mode_indicator, len(mode_indicator), curses.color_pair(4))
        except curses.error:
            pass

        # File list
        items = self.get_current_list()
        list_height = h - 5  # Header, path, help, message, status

        # Adjust scroll
        if self.cursor < self.scroll_offset:
            self.scroll_offset = self.cursor
        elif self.cursor >= self.scroll_offset + list_height:
            self.scroll_offset = self.cursor - list_height + 1

        # Choose colors based on mode
        if self.mode == "remote":
            selected_color = curses.color_pair(7)   # Magenta selection for remote
            dir_color = curses.color_pair(8)        # Magenta directories for remote
        else:
            selected_color = curses.color_pair(10)  # Green selection for local
            dir_color = curses.color_pair(11)       # Green directories for local

        for i in range(list_height):
            idx = i + self.scroll_offset
            y = i + 2

            if idx < len(items):
                item = items[idx]
                is_selected = (idx == self.cursor)

                # Format line
                if item['is_dir']:
                    icon = "📁 "
                    name = item['name'] + "/"
                    size_str = "     <DIR>"
                else:
                    icon = "📄 "
                    name = item['name']
                    size_str = self.format_size(item['size'])

                line = f" {icon}{name}"
                padding = w - len(line) - len(size_str) - 2
                if padding > 0:
                    line += " " * padding + size_str + " "
                else:
                    line = line[:w-1]

                if is_selected:
                    self.stdscr.addnstr(y, 0, line.ljust(w), w, selected_color | curses.A_BOLD)
                elif item['is_dir']:
                    self.stdscr.addnstr(y, 0, line, w, dir_color)
                else:
                    self.stdscr.addnstr(y, 0, line, w)

        # Help bar - show relevant actions based on mode
        help_y = h - 2
        if self.connected:
            if self.mode == "remote":
                help_text = " ↑↓:Nav │ Enter:Open │ d:Down │ D:Del │ r:Rename │ m:Mkdir │ /:Search │ v:View │ e:Edit │ Tab:Local │ c:Disc │ q:Quit "
            else:
                help_text = " ↑↓:Nav │ Enter:Open │ u:Upload │ D:Del │ r:Rename │ m:Mkdir │ /:Search │ Tab:Remote │ c:Disc │ q:Quit "
        else:
            help_text = " c:Connect │ s:Set Server │ Tab:Switch View │ q:Quit "
        try:
            self.stdscr.addnstr(help_y, 0, help_text.center(w)[:w-1], w-1, curses.color_pair(4))
        except curses.error:
            pass

        # Message bar / Progress bar
        msg_y = h - 1
        try:
            if self.transfer_active:
                # Calculate speed
                current_time = time.time()
                if current_time - self.transfer_last_time >= 0.5:  # Update speed every 0.5s
                    bytes_diff = self.transfer_progress - self.transfer_last_progress
                    time_diff = current_time - self.transfer_last_time
                    if time_diff > 0:
                        self.transfer_speed = bytes_diff / time_diff
                    self.transfer_last_progress = self.transfer_progress
                    self.transfer_last_time = current_time

                # Show progress bar
                percent = self.transfer_progress / self.transfer_total if self.transfer_total > 0 else 0
                bar_width = min(30, w - 70)
                filled = int(bar_width * percent)
                bar = '█' * filled + '░' * (bar_width - filled)

                size_str = f"{self.format_size(self.transfer_progress).strip()}/{self.format_size(self.transfer_total).strip()}"
                speed_str = f"{self.format_size(self.transfer_speed).strip()}/s"
                max_name = 18
                display_name = self.transfer_filename[:max_name-2] + '..' if len(self.transfer_filename) > max_name else self.transfer_filename

                progress_text = f" {self.transfer_action}: {display_name}  [{bar}] {percent:>5.1%}  {size_str}  {speed_str}  (x to cancel)"
                self.stdscr.addnstr(msg_y, 0, progress_text.ljust(w-1), w-1, curses.color_pair(1) | curses.A_BOLD)
            elif self.message:
                if self.message_type == "success":
                    color = curses.color_pair(2)
                elif self.message_type == "error":
                    color = curses.color_pair(3)
                else:
                    color = curses.color_pair(1)
                self.stdscr.addnstr(msg_y, 0, f" {self.message}".ljust(w-1), w-1, color)
            else:
                self.stdscr.addnstr(msg_y, 0, " " * (w-1), w-1)
        except curses.error:
            pass

        self.stdscr.refresh()

    def confirm(self, prompt, modal_type="default"):
        h, w = self.stdscr.getmaxyx()

        # Choose color based on modal type
        if modal_type == "delete":
            border_color = curses.color_pair(12)  # Red for delete
            title = "⚠️  DELETE"
        elif modal_type == "upload":
            border_color = curses.color_pair(13)  # Cyan for upload
            title = "📤 UPLOAD"
        elif modal_type == "download":
            border_color = curses.color_pair(14)  # Green for download
            title = "📥 DOWNLOAD"
        else:
            border_color = curses.color_pair(4)   # Yellow default
            title = "CONFIRM"

        # Modal dimensions
        modal_width = min(max(len(prompt) + 10, len(title) + 10), w - 4)
        modal_height = 6
        start_y = (h - modal_height) // 2
        start_x = (w - modal_width) // 2

        # Draw modal box
        try:
            # Top border with title
            top_border = "╔" + "═" * ((modal_width - len(title) - 4) // 2) + f" {title} " + "═" * ((modal_width - len(title) - 3) // 2) + "╗"
            self.stdscr.addnstr(start_y, start_x, top_border[:modal_width], modal_width, border_color | curses.A_BOLD)

            # Empty line
            self.stdscr.addnstr(start_y + 1, start_x, "║" + " " * (modal_width - 2) + "║", modal_width, border_color | curses.A_BOLD)

            # Prompt line
            prompt_text = prompt[:modal_width - 4].center(modal_width - 2)
            self.stdscr.addnstr(start_y + 2, start_x, "║", 1, border_color | curses.A_BOLD)
            self.stdscr.addnstr(start_y + 2, start_x + 1, prompt_text, modal_width - 2)
            self.stdscr.addnstr(start_y + 2, start_x + modal_width - 1, "║", 1, border_color | curses.A_BOLD)

            # Empty line
            self.stdscr.addnstr(start_y + 3, start_x, "║" + " " * (modal_width - 2) + "║", modal_width, border_color | curses.A_BOLD)

            # Buttons line
            buttons = "  [Enter] Yes    [Esc] No  "
            buttons_text = buttons.center(modal_width - 2)
            self.stdscr.addnstr(start_y + 4, start_x, "║", 1, border_color | curses.A_BOLD)
            self.stdscr.addnstr(start_y + 4, start_x + 1, buttons_text, modal_width - 2, curses.color_pair(2) | curses.A_BOLD)
            self.stdscr.addnstr(start_y + 4, start_x + modal_width - 1, "║", 1, border_color | curses.A_BOLD)

            # Bottom border
            self.stdscr.addnstr(start_y + 5, start_x, "╚" + "═" * (modal_width - 2) + "╝", modal_width, border_color | curses.A_BOLD)

        except curses.error:
            pass

        self.stdscr.refresh()
        key = self.stdscr.getch()
        result = key in (curses.KEY_ENTER, 10, 13, ord('y'), ord('Y'))

        # Redraw screen to clear modal
        self.draw()

        return result

    def search_files(self):
        """Search for files in current view"""
        query = self.get_input("Search: ")
        if not query:
            return

        query_lower = query.lower()
        items = self.get_current_list()

        # Find matches
        matches = []
        for idx, item in enumerate(items):
            if item['name'] != '..' and query_lower in item['name'].lower():
                matches.append(idx)

        if not matches:
            self.set_message(f"No results for '{query}'", "info")
            return

        # Jump to first match
        self.cursor = matches[0]
        self.set_message(f"Found {len(matches)} result(s) for '{query}'", "success")

    def run(self):
        self.refresh_local()

        while True:
            self.draw()

            # Use timeout for non-blocking input during transfers
            if self.transfer_active:
                self.stdscr.timeout(100)  # 100ms timeout for responsive progress updates
            else:
                self.stdscr.timeout(-1)  # Blocking

            key = self.stdscr.getch()

            # Handle 'x' during transfer - cancel it
            if key == ord('x') and self.transfer_active:
                self.transfer_cancelled = True
                self.set_message("Cancelling transfer...", "info")
                continue

            if key == -1:  # No input (timeout)
                continue

            items = self.get_current_list()
            max_cursor = len(items) - 1 if items else 0

            if key == ord('q') or key == ord('Q'):
                if self.connected:
                    self.disconnect()
                break

            elif key == curses.KEY_UP or key == ord('k'):
                if self.cursor > 0:
                    self.cursor -= 1

            elif key == curses.KEY_DOWN or key == ord('j'):
                if self.cursor < max_cursor:
                    self.cursor += 1

            elif key == curses.KEY_PPAGE:  # Page Up
                self.cursor = max(0, self.cursor - 10)

            elif key == curses.KEY_NPAGE:  # Page Down
                self.cursor = min(max_cursor, self.cursor + 10)

            elif key == curses.KEY_HOME:
                self.cursor = 0
                self.scroll_offset = 0

            elif key == curses.KEY_END:
                self.cursor = max_cursor

            elif key in (curses.KEY_ENTER, 10, 13, curses.KEY_RIGHT, ord('l')):
                self.enter_directory()

            elif key in (curses.KEY_LEFT, ord('h'), curses.KEY_BACKSPACE, 127):
                # Go to parent
                self.cursor = 0
                self.enter_directory()

            elif key == ord('\t'):  # Tab - switch mode
                self.mode = "local" if self.mode == "remote" else "remote"
                self.cursor = 0
                self.scroll_offset = 0
                if self.mode == "remote":
                    self.refresh_remote()
                else:
                    self.refresh_local()

            elif key == ord('c') or key == ord('C'):
                if not self.connected:
                    self.connect()
                else:
                    self.disconnect()

            elif key == ord('s') or key == ord('S'):
                if not self.connected:
                    self.set_server()

            elif key == ord('u'):  # Upload
                self.upload_selected()

            elif key == ord('d'):  # Download
                self.download_selected()

            elif key == ord('D'):  # Delete
                item = self.get_selected_item()
                if item and item['name'] != '..':
                    if self.confirm(f"Delete '{item['name']}'?", "delete"):
                        self.delete_selected()

            elif key == ord('r'):  # Rename
                self.rename_selected()

            elif key == ord('m'):  # Make directory
                self.make_directory()

            elif key == ord('v'):  # View
                self.view_file()

            elif key == ord('e'):  # Edit
                self.edit_file()

            elif key == ord('R'):  # Refresh
                if self.mode == "remote":
                    self.refresh_remote()
                else:
                    self.refresh_local()
                self.set_message("Refreshed", "info")

            elif key == ord('f') or key == ord('/'):  # Search
                self.search_files()

def main(stdscr):
    manager = FTPManager(stdscr)

    # Parse command line for quick connect
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith("ftp://"):
            arg = arg[6:].rstrip('/')
            if ':' in arg:
                host, port = arg.rsplit(':', 1)
                manager.host = host
                try:
                    manager.port = int(port)
                except ValueError:
                    pass
            else:
                manager.host = arg

    # Auto-connect on startup
    manager.connect()

    # If connection failed, prompt for server address
    if not manager.connected:
        manager.set_message("Connection failed. Press 's' to set server address.", "error")

    manager.run()

if __name__ == "__main__":
    curses.wrapper(main)
