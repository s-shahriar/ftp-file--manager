#!/usr/bin/env python3
"""
Quick FTP Send - Upload files/folders to FTP server instantly
Usage: ftpsend file1 folder1 file2 ...
"""

import sys
import ftplib
import os
from pathlib import Path

# Default FTP settings - Change these to your FTP server
HOST = "192.168.0.103"  # Your FTP server IP
PORT = 9999             # Your FTP server port
USER = "anonymous"
PASS = ""

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BLUE = '\033[94m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"

def progress_bar(current, total, filename, width=35):
    percent = current / total if total > 0 else 1
    filled = int(width * percent)
    bar = '█' * filled + '░' * (width - filled)
    size_info = f"{format_size(current)}/{format_size(total)}"

    # Truncate filename if too long
    max_name = 22
    display_name = filename[:max_name-2] + '..' if len(filename) > max_name else filename

    sys.stdout.write(f'\r  {display_name:<22} {CYAN}[{bar}]{RESET} {percent:>6.1%} {DIM}{size_info}{RESET}')
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
                pass  # Directory might already exist

def upload_file(ftp, local_path, remote_dir=""):
    """Upload a single file with progress bar"""
    file_size = local_path.stat().st_size
    uploaded = [0]

    def callback(data):
        uploaded[0] += len(data)
        progress_bar(uploaded[0], file_size, local_path.name)

    if remote_dir:
        ensure_remote_dir(ftp, remote_dir)
        ftp.cwd('/' + remote_dir)

    with open(local_path, 'rb') as f:
        ftp.storbinary(f'STOR {local_path.name}', f, blocksize=8192, callback=callback)

    # Return to root
    ftp.cwd('/')
    print(f" {GREEN}✓{RESET}")

def upload_folder(ftp, folder_path, base_remote=""):
    """Recursively upload a folder"""
    folder_name = folder_path.name
    remote_base = f"{base_remote}/{folder_name}" if base_remote else folder_name

    print(f"\n  {BLUE}📁 {folder_name}/{RESET}")

    files_uploaded = 0
    errors = 0

    # Get all items sorted (folders first, then files)
    items = sorted(folder_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

    for item in items:
        if item.is_file():
            try:
                upload_file(ftp, item, remote_base)
                files_uploaded += 1
            except Exception as e:
                print(f" {RED}✗ {e}{RESET}")
                errors += 1
        elif item.is_dir():
            # Recursive call for subdirectories
            sub_uploaded, sub_errors = upload_folder(ftp, item, remote_base)
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

def send_files(items):
    if not items:
        print(f"{YELLOW}Usage: ftpsend <file1> [folder1] [file2] ...{RESET}")
        sys.exit(1)

    # Validate items first
    valid_items = []
    for item in items:
        path = Path(item)
        if not path.exists():
            print(f"{RED}✗ Not found: {item}{RESET}")
        else:
            valid_items.append(path)

    if not valid_items:
        print(f"{RED}No valid files/folders to send{RESET}")
        sys.exit(1)

    # Calculate total stats
    total_files = 0
    total_size = 0
    for path in valid_items:
        files, size = collect_stats(path)
        total_files += files
        total_size += size

    print(f"{DIM}Total: {total_files} file(s), {format_size(total_size)}{RESET}\n")

    # Connect and upload
    try:
        print(f"{YELLOW}Connecting to {HOST}:{PORT}...{RESET}")
        ftp = ftplib.FTP()
        ftp.connect(HOST, PORT, timeout=10)
        ftp.login(USER, PASS)
        print(f"{GREEN}✓ Connected{RESET}")

        success = 0
        errors = 0

        for path in valid_items:
            if path.is_file():
                try:
                    upload_file(ftp, path)
                    success += 1
                except Exception as e:
                    print(f" {RED}✗ {e}{RESET}")
                    errors += 1
            elif path.is_dir():
                uploaded, errs = upload_folder(ftp, path)
                success += uploaded
                errors += errs

        ftp.quit()

        print()
        if errors == 0:
            print(f"{GREEN}{BOLD}✓ Sent {success} file(s) successfully!{RESET}")
        else:
            print(f"{YELLOW}Sent {success} file(s), {errors} failed{RESET}")

    except Exception as e:
        print(f"{RED}Connection failed: {e}{RESET}")
        print(f"\n{DIM}Press Enter to close...{RESET}")
        input()
        sys.exit(1)

    # Wait for user to close
    print(f"\n{DIM}Press Enter to close...{RESET}")
    input()

if __name__ == "__main__":
    send_files(sys.argv[1:])
