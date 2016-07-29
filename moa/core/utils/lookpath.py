# _*_ coding:UTF-8 _*_
import platform
import os


def look_path(program):
    system = platform.system()

    def is_exe(fpath):
        if system.startswith('Windows') and not fpath.lower().endswith('.exe'):
            fpath += '.exe'
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def get_adb_path():
    system = platform.system()
    base_path = os.path.dirname(os.path.realpath(__file__))
    base_path = os.path.join(base_path, "..", "android", "adb")
    moa_adb_path = {
        "Windows": os.path.join("windows", "adb.exe"),
        "Darwin": os.path.join("mac", "adb"),
        "Linux": os.path.join("linux", "adb")
    }
    moa_adb = os.path.join(base_path, moa_adb_path[system])
    # overwrite uiautomator adb
    if "ANDROID_HOME" in os.environ:
        del os.environ["ANDROID_HOME"]
    os.environ["PATH"] = os.path.dirname(moa_adb) + os.pathsep + os.environ["PATH"]
    return moa_adb
