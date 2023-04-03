# encoding=utf-8
"""
MIT License

Copyright (c) 2021 zackees

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

    refer to: https://github.com/zackees/static_ffmpeg

    Entry point for running the ffmpeg executable.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import subprocess
import os
import stat
import sys
import zipfile
from datetime import datetime

import requests  # type: ignore
from filelock import FileLock, Timeout

TIMEOUT = 10 * 60  # Wait upto 10 minutes to validate install
# otherwise break the lock and install anyway.

SELF_DIR = os.path.abspath(os.path.dirname(__file__))
LOCK_FILE = os.path.join(SELF_DIR, "lock.file")


PLATFORM_ZIP_FILES = {
    "win32": "/raw/main/v5.0/win32.zip",
    "darwin": "/raw/main/v5.0/darwin.zip",
    "linux": "/raw/main/v5.0/linux.zip",
}

BACKUP_PLATFORM_ZIP_FILES = {
    "win32": "/downloads/ffmpeg_bins/v5.0/win32.zip",
    "darwin": "/downloads/ffmpeg_bins/v5.0/darwin.zip",
    "linux": "/downloads/ffmpeg_bins/v5.0/linux.zip",
}

def check_system():
    """Friendly error if there's a problem with the system configuration."""
    if sys.platform not in PLATFORM_ZIP_FILES:
        raise OSError("Please implement static_ffmpeg for %s"%sys.platform)

def get_platform_http_zip():
    """Return the download link for the current platform"""
    check_system()
    try:
        MAIN_SIT = "https://github.com/zackees/ffmpeg_bins"
        r = requests.get(MAIN_SIT, timeout=10)
        r.raise_for_status()
        return MAIN_SIT + PLATFORM_ZIP_FILES[sys.platform]
    except:
        print("Warning, main url download fail, try backup url.")
        BACKUP_SIT = "https://airtestproject.s3.netease.com"
        return BACKUP_SIT + BACKUP_PLATFORM_ZIP_FILES[sys.platform]
    
def get_platform_dir():
    """Either get the executable or raise an error"""
    check_system()
    return os.path.join(SELF_DIR, "bin", sys.platform)


def download_file(url, local_path):
    """Downloads a file to the give path."""
    # NOTE the stream=True parameter below
    print("Downloading and save to %s" % local_path)
    with requests.get(url, stream=True) as req:
        req.raise_for_status()
        with open(local_path, "wb") as file_d:
            for chunk in req.iter_content(chunk_size=8192 * 16):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                # sys.stdout.write(".")
                file_d.write(chunk)
        print("Download completed.")
    return local_path


def get_or_fetch_platform_executables_else_raise(fix_permissions=True):
    """Either get the executable or raise an error"""
    lock = FileLock(LOCK_FILE, timeout=TIMEOUT)  # pylint: disable=E0110
    try:
        with lock.acquire():
            return _get_or_fetch_platform_executables_else_raise_no_lock(
                fix_permissions=fix_permissions
            )
    except Timeout:
        sys.stderr.write(
            "%s: Warning, could not acquire lock at %s\n"
        )%(__file__, LOCK_FILE)
        return _get_or_fetch_platform_executables_else_raise_no_lock(
            fix_permissions=fix_permissions
        )


def _get_or_fetch_platform_executables_else_raise_no_lock(fix_permissions=True):
    """Either get the executable or raise an error, internal api"""
    exe_dir = get_platform_dir()
    installed_crumb = os.path.join(exe_dir, "installed.crumb")
    if not os.path.exists(installed_crumb):
        print("\n===========ffmpeg is missing, fetching it now.=============\n")
        # All zip files store their platform executables in a folder
        # like "win32" or "darwin" or "linux" inside the executable. So root
        # the install one level up from that same directory.
        install_dir = os.path.dirname(exe_dir)
        try:
            os.makedirs(exe_dir)#, exist_ok=True)
        except:
            pass
        local_zip = exe_dir + ".zip"
        url = get_platform_http_zip()
        download_file(url, local_zip)
        print("Extracting %s -> %s"%(local_zip, install_dir))
        with zipfile.ZipFile(local_zip, mode="r") as zipf:
            zipf.extractall(install_dir)
        try:
            os.remove(local_zip)
        except OSError as err:
            print("%s: Error could not remove %s because of %s"%(__file__, local_zip, err))
        with open(installed_crumb, "wt") as filed:  # pylint: disable=W1514
            filed.write("installed from %s on %s"%(url, datetime.now().__str__()))
        print("=============================================================\n")
    ffmpeg_exe = os.path.join(exe_dir, "ffmpeg")
    ffprobe_exe = os.path.join(exe_dir, "ffprobe")
    if sys.platform == "win32":
        ffmpeg_exe = "%s.exe"%ffmpeg_exe
        ffprobe_exe = "%s.exe"%ffprobe_exe
    for exe in [ffmpeg_exe, ffprobe_exe]:
        if (
            fix_permissions
            and sys.platform != "win32"
            and (not os.access(exe, os.X_OK) or not os.access(exe, os.R_OK))
        ):
            # Set bits for execution and read for all users.
            exe_bits = stat.S_IXOTH | stat.S_IXUSR | stat.S_IXGRP
            read_bits = stat.S_IRUSR | stat.S_IRGRP | stat.S_IXGRP
            os.chmod(exe, exe_bits | read_bits)
            assert os.access(exe, os.X_OK), "Could not execute %s"%exe
            assert os.access(exe, os.R_OK), "Could not get read bits of %s"%exe
    return ffmpeg_exe, ffprobe_exe


def main_static_ffmpeg():
    """Entry point for running static_ffmpeg, which delegates to ffmpeg."""
    ffmpeg_exe, _ = get_or_fetch_platform_executables_else_raise()
    rtn = subprocess.call([ffmpeg_exe] + sys.argv[1:])
    sys.exit(rtn)


def main_static_ffprobe():
    """Entry point for running static_ffmpeg, which delegates to ffmpeg."""
    _, ffprobe = get_or_fetch_platform_executables_else_raise()
    rtn = subprocess.call([ffprobe] + sys.argv[1:])
    sys.exit(rtn)


def main_print_paths():
    """Entry point for printing ffmpeg paths"""
    ffmpeg_exe, ffprobe_exe = get_or_fetch_platform_executables_else_raise()
    print("FFMPEG=%s"%ffmpeg_exe)
    print("FFPROBE=%s"%ffprobe_exe)
    sys.exit(0)

def add_paths():
    """Add the ffmpeg executable to the path"""
    ffmpeg, _ = get_or_fetch_platform_executables_else_raise()
    os.environ["PATH"] = os.pathsep.join([str(os.path.dirname(ffmpeg)), os.environ["PATH"]])

if __name__ == "__main__":
    # get_or_fetch_platform_executables_else_raise()
    add_paths()
