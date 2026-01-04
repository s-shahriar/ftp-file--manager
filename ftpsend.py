#!/usr/bin/env python3
"""
Quick FTP Send - Upload files/folders to FTP server instantly
Usage: ftpsend file1 folder1 file2 ...
"""

import sys
import ftplib
import os
import time
import signal
import threading
import json
import readline
from pathlib import Path

# Global cancel flag
cancelled = False

# Config file to remember last successful connection
CONFIG_FILE = Path.home() / ".ftpsend_config.json"

# Default FTP settings
DEFAULT_HOST = "192.168.0.103"
DEFAULT_PORT = 9999
USER = "anonymous"
PASS = ""

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

# Load saved config
HOST, PORT = load_config()

# ANSI colors and styles
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
PURPLE = '\033[38;5;141m'
ORANGE = '\033[38;5;208m'
WHITE = '\033[97m'
GRAY = '\033[90m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'

def clear_screen():
        print('\033[2J\033[H', end='')

def handle_cancel(signum, frame):
        """Handle Ctrl+C to cancel transfer"""
        global cancelled
        cancelled = True
        print(f"\n\n      {YELLOW}⚠ Cancelling transfer...{RESET}")

signal.signal(signal.SIGINT, handle_cancel)

def get_terminal_width():
        try:
            return os.get_terminal_size().columns
        except:
            return 80

def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

def draw_header():
        print()
        print()
        print(f"  {BOLD}{PURPLE}╔════════════════════════════════════════════════════════╗{RESET}")
        print(f"  {BOLD}{PURPLE}║{RESET}                                                        {BOLD}{PURPLE}║{RESET}")
        print(f"  {BOLD}{PURPLE}║{RESET}     {BOLD}{CYAN}▓▓▓{RESET}  {BOLD}{WHITE}F T P   F I L E   S E N D E R{RESET}  {BOLD}{CYAN}▓▓▓{RESET}     {BOLD}{PURPLE}║{RESET}")
        print(f"  {BOLD}{PURPLE}║{RESET}                                                        {BOLD}{PURPLE}║{RESET}")
        print(f"  {BOLD}{PURPLE}╚════════════════════════════════════════════════════════╝{RESET}")
        print()
        print(f"      {BOLD}{GREEN}◉{RESET} {BOLD}Server:{RESET} {CYAN}{HOST}{RESET}:{YELLOW}{PORT}{RESET}")
        print()
        print(f"  {DIM}(Press Ctrl+C to cancel transfer){RESET}")
        print()

def draw_section(title, color=CYAN):
        print(f"  {color}{BOLD}━━━ {title.upper()} {'━' * (48 - len(title))}{RESET}")

def get_input(prompt, default=""):
        """Get user input with optional default value prefilled"""
        def prefill_hook():
            readline.insert_text(default)
            readline.redisplay()

        if default:
            print(f"      {BOLD}{CYAN}{prompt}{RESET}  ", end="")
            readline.set_startup_hook(prefill_hook)
            try:
                value = input().strip()
                readline.set_startup_hook()
                return value if value else default
            except (EOFError, KeyboardInterrupt):
                readline.set_startup_hook()
                return default
        else:
            print(f"      {BOLD}{CYAN}{prompt}{RESET}  ", end="")
            try:
                return input().strip()
            except (EOFError, KeyboardInterrupt):
                return ""

def change_server():
        """Let user change server settings"""
        global HOST, PORT
        clear_screen()
        print()
        print()
        print(f"  {BOLD}{PURPLE}╔════════════════════════════════════════════════════════╗{RESET}")
        print(f"  {BOLD}{PURPLE}║{RESET}                                                        {BOLD}{PURPLE}║{RESET}")
        print(f"  {BOLD}{PURPLE}║{RESET}            {BOLD}{WHITE}S E R V E R   C O N F I G{RESET}                {BOLD}{PURPLE}║{RESET}")
        print(f"  {BOLD}{PURPLE}║{RESET}                                                        {BOLD}{PURPLE}║{RESET}")
        print(f"  {BOLD}{PURPLE}╚════════════════════════════════════════════════════════╝{RESET}")
        print()
        print()

        new_host = get_input("Server IP:", HOST)
        if new_host:
            HOST = new_host

        print()
        new_port = get_input("Port:", str(PORT))
        if new_port:
            try:
                PORT = int(new_port)
            except ValueError:
                pass

        print()
        print()
        print(f"      {BOLD}{GREEN}✓{RESET} Configuration saved!")
        print(f"      {GRAY}New server:{RESET} {CYAN}{HOST}{RESET}:{YELLOW}{PORT}{RESET}")
        print()
        import time
        time.sleep(1.5)

def progress_bar(current, total, filename, start_time, queue_info="", width=30):
        percent = current / total if total > 0 else 1
        filled = int(width * percent)
        bar = '█' * filled + '░' * (width - filled)

        # Calculate speed
        elapsed = time.time() - start_time
        speed = current / elapsed if elapsed > 0 else 0
        speed_str = f"{format_size(speed)}/s"

        # Size info
        size_info = f"{format_size(current)}/{format_size(total)}"

        # Truncate filename if too long
        max_name = 18 if queue_info else 20
        display_name = filename[:max_name-2] + '..' if len(filename) > max_name else filename

        # Add queue info if provided
        prefix = f"{CYAN}{queue_info}{RESET} " if queue_info else ""

        sys.stdout.write(f'\r      {prefix}{WHITE}{display_name:<{max_name}}{RESET} {CYAN}[{bar}]{RESET} {GREEN}{percent:>5.1%}{RESET} {DIM}{size_info} @ {speed_str}{RESET}')
        sys.stdout.flush()

def ensure_remote_dir(ftp, remote_path):
        """Create remote directory structure if it doesn't exist"""
        dirs = remote_path.split('/')
        current = ""
        for d in dirs:
            if not d:
                continue
            current += "/" + d
            try:
                ftp.cwd(current)
            except ftplib.error_perm:
                try:
                    ftp.mkd(current)
                except ftplib.error_perm:
                    pass

def upload_file(ftp, local_path, remote_dir="", queue_info=""):
        """Upload a single file with progress bar"""
        global cancelled
        if cancelled:
            raise Exception("Cancelled")

        file_size = local_path.stat().st_size
        uploaded = [0]
        start_time = time.time()

        def callback(data):
            if cancelled:
                raise Exception("Cancelled")
            uploaded[0] += len(data)
            progress_bar(uploaded[0], file_size, local_path.name, start_time, queue_info)

        if remote_dir:
            ensure_remote_dir(ftp, remote_dir)
            ftp.cwd('/' + remote_dir)

        with open(local_path, 'rb') as f:
            ftp.storbinary(f'STOR {local_path.name}', f, blocksize=8192, callback=callback)

        ftp.cwd('/')

        elapsed = time.time() - start_time
        print(f" {BOLD}{GREEN}✓{RESET} {DIM}({elapsed:.1f}s){RESET}")

def upload_folder(ftp, folder_path, base_remote="", queue_info=""):
        """Recursively upload a folder"""
        global cancelled
        if cancelled:
            return 0, 0

        folder_name = folder_path.name
        remote_base = f"{base_remote}/{folder_name}" if base_remote else folder_name

        print(f"\n      {BLUE}📁 {BOLD}{folder_name}/{RESET}")

        files_uploaded = 0
        errors = 0

        items = sorted(folder_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

        for item in items:
            if cancelled:
                break
            if item.is_file():
                try:
                    upload_file(ftp, item, remote_base, queue_info)
                    files_uploaded += 1
                except Exception as e:
                    if "Cancelled" not in str(e):
                        print(f" {RED}✗ {e}{RESET}")
                        errors += 1
                    break
            elif item.is_dir():
                sub_uploaded, sub_errors = upload_folder(ftp, item, remote_base, queue_info)
                files_uploaded += sub_uploaded
                errors += sub_errors

        return files_uploaded, errors

def collect_stats(path):
        """Count files and total size in a path"""
        if path.is_file():
            return 1, path.stat().st_size

        total_files = 0
        total_size = 0
        for item in path.rglob('*'):
            if item.is_file():
                total_files += 1
                total_size += item.stat().st_size
        return total_files, total_size

def draw_result_box(success, errors, total_time, was_cancelled=False):
        if was_cancelled:
            color = YELLOW
            icon = "⚠"
            status = "TRANSFER CANCELLED"
        elif errors == 0:
            color = GREEN
            icon = "✓"
            status = "TRANSFER COMPLETE"
        else:
            color = YELLOW
            icon = "⚠"
            status = "TRANSFER FINISHED WITH ERRORS"

        print()
        print()
        print(f"  {BOLD}{color}╔════════════════════════════════════════════════════════╗{RESET}")
        print(f"  {BOLD}{color}║{RESET}                                                        {BOLD}{color}║{RESET}")
        print(f"  {BOLD}{color}║{RESET}              {BOLD}{WHITE}{icon}  {status}{RESET}              {BOLD}{color}║{RESET}")
        print(f"  {BOLD}{color}║{RESET}                                                        {BOLD}{color}║{RESET}")
        print(f"  {BOLD}{color}╚════════════════════════════════════════════════════════╝{RESET}")
        print()

        # Stats
        if was_cancelled:
            stats = f"{success} file(s) sent before cancel"
        else:
            stats = f"{success} file(s) sent"
            if errors > 0:
                stats += f", {errors} failed"
        stats += f" in {total_time:.1f}s"

        print(f"      {DIM}{stats}{RESET}")
        print()

def send_files(items):
        global cancelled
        clear_screen()
        draw_header()

        if not items:
            print(f"      {YELLOW}Usage: ftpsend <file1> [folder1] [file2] ...{RESET}")
            print(f"\n      {DIM}Press Enter to close...{RESET}")
            input()
            sys.exit(1)

        # Validate items
        valid_items = []
        for item in items:
            path = Path(item)
            if not path.exists():
                print(f"      {RED}✗ Not found: {item}{RESET}")
            else:
                valid_items.append(path)

        if not valid_items:
            print(f"\n      {RED}No valid files/folders to send{RESET}")
            print(f"\n      {DIM}Press Enter to close...{RESET}")
            input()
            sys.exit(1)

        # Calculate total stats
        total_files = 0
        total_size = 0
        for path in valid_items:
            files, size = collect_stats(path)
            total_files += files
            total_size += size

        draw_section("FILES TO SEND", GREEN)
        print()
        for path in valid_items:
            if path.is_dir():
                files, size = collect_stats(path)
                print(f"      {BLUE}📁{RESET} {path.name}/ {DIM}({files} files, {format_size(size)}){RESET}")
            else:
                print(f"      {WHITE}📄{RESET} {path.name} {DIM}({format_size(path.stat().st_size)}){RESET}")

        print(f"\n      {BOLD}Total:{RESET} {total_files} file(s), {format_size(total_size)}")
        print()

        # Connect with retry option
        ftp = None
        while True:
            print()
            draw_section("CONNECTING", ORANGE)
            print()
            print(f"      {ORANGE}⟳{RESET} Connecting to {CYAN}{HOST}{RESET}:{YELLOW}{PORT}{RESET}...")

            overall_start = time.time()

            try:
                ftp = ftplib.FTP()
                ftp.connect(HOST, PORT, timeout=10)
                ftp.login(USER, PASS)
                print(f"      {BOLD}{GREEN}✓{RESET} Connected successfully!")
                print()

                # Save successful connection
                save_config(HOST, PORT)
                break  # Connection successful, exit loop
            except Exception as e:
                print(f"      {BOLD}{RED}✗{RESET} Connection failed: {DIM}{e}{RESET}")
                print()
                print(f"  {GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
                print()
                print(f"      {BOLD}{ORANGE}S{RESET}  {BOLD}Server{RESET}   {GRAY}→{RESET}   Change server address")
                print()
                print(f"      {BOLD}{ORANGE}R{RESET}  {BOLD}Retry{RESET}    {GRAY}→{RESET}   Retry connection")
                print()
                print(f"      {BOLD}{ORANGE}Q{RESET}  {BOLD}Quit{RESET}     {GRAY}→{RESET}   Exit")
                print()
                print(f"  {GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
                print()
                print(f"      {BOLD}{CYAN}›{RESET} ", end="")

                try:
                    choice = input().strip().lower()
                except (EOFError, KeyboardInterrupt):
                    choice = 'q'

                if choice == 's':
                    change_server()
                    continue
                elif choice == 'r':
                    continue
                else:
                    print()
                    sys.exit(1)

        # Transfer files
        draw_section("TRANSFERRING", GREEN)

        success = 0
        errors = 0

        # Show queue info if multiple items
        total_items = len(valid_items)
        show_queue = total_items > 1

        try:
            for idx, path in enumerate(valid_items):
                if cancelled:
                    break

                # Generate queue info
                queue_info = f"[{idx + 1}/{total_items}]" if show_queue else ""

                if path.is_file():
                    try:
                        upload_file(ftp, path, queue_info=queue_info)
                        success += 1
                    except Exception as e:
                        if "Cancelled" not in str(e):
                            print(f" {RED}✗ {e}{RESET}")
                            errors += 1
                        break
                elif path.is_dir():
                    uploaded, errs = upload_folder(ftp, path, queue_info=queue_info)
                    success += uploaded
                    errors += errs

            try:
                ftp.quit()
            except:
                pass

            total_time = time.time() - overall_start
            draw_result_box(success, errors, total_time, cancelled)

            # Auto-close on cancel, wait for Enter on success
            if cancelled:
                print(f"\n  {DIM}Closing...{RESET}")
                time.sleep(1)
            else:
                print(f"\n  {DIM}Press Enter to close...{RESET}")
                input()

        except Exception as e:
            if "Cancelled" in str(e):
                total_time = time.time() - overall_start
                draw_result_box(0, 0, total_time, True)
                print(f"\n  {DIM}Closing...{RESET}")
                time.sleep(1)
            else:
                print(f"    {RED}✗ Transfer error: {e}{RESET}")
                print(f"\n  {DIM}Press Enter to close...{RESET}")
                input()
            sys.exit(1)

if __name__ == "__main__":
        send_files(sys.argv[1:])
