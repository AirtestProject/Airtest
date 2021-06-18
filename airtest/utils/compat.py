import sys
import os
import subprocess
import threading
from six import PY3, raise_from, reraise


EXT = ".air"  # script dir extension
DEFAULT_LOG_DIR = "log"  # <script_dir>/log


if PY3:
    def decode_path(path):
        return path
else:
    def decode_path(path):
        return path.decode(sys.getfilesystemencoding()) if path else path


if sys.platform.startswith("win"):
    # Don't display the Windows GPF dialog if the invoked program dies.
    try:
        SUBPROCESS_FLAG = subprocess.CREATE_NO_WINDOW  # in Python 3.7+
    except AttributeError:
        import ctypes
        SEM_NOGPFAULTERRORBOX = 0x0002  # From MSDN
        ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX)  # win32con.CREATE_NO_WINDOW?
        SUBPROCESS_FLAG = 0x8000000
else:
    SUBPROCESS_FLAG = 0


def script_dir_name(script_path):
    """get script dir for old & new cli api compatibility"""
    script_path = os.path.normpath(decode_path(script_path))
    if script_path.endswith(EXT):
        path = script_path
        name = os.path.basename(script_path).replace(EXT, ".py")
    else:
        path = os.path.dirname(script_path) or "."
        name = os.path.basename(script_path)
    return path, name


def script_log_dir(script_path, logdir):
    if logdir is True:
        logdir = os.path.join(script_path, DEFAULT_LOG_DIR)
    elif logdir:
        logdir = decode_path(logdir)
    return logdir


def raisefrom(exc_type, message, exc):
    if sys.version_info[:2] >= (3, 2):
        raise_from(exc_type(message), exc)
    else:
        reraise(exc_type, '%s - %s' % (message, exc), sys.exc_info()[2])


def proc_communicate_timeout(proc, timeout):
    """
    Enable subprocess.Popen to accept timeout parameters, compatible with py2 and py3

    :param proc: subprocess.Popen()
    :param timeout: timeout in seconds
    :return: result of proc.communicate()
    :raises: RuntimeError when timeout
    """
    if sys.version_info[:2] >= (3, 3):
        # in Python 3.3+
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as e:
            proc.kill()
            stdout, stderr = proc.communicate()
            exp = RuntimeError("Command {cmd} timed out after {timeout} seconds: stdout['{stdout}'], "
                                    "stderr['{stderr}']".format(cmd=proc.args, timeout=e.timeout,
                                                                stdout=stdout, stderr=stderr))
            raise_from(exp, None)
    else:
        timer = threading.Timer(timeout, proc.kill)
        try:
            timer.start()
            stdout, stderr = proc.communicate()
        finally:
            timer.cancel()
            if proc.returncode > 0:
                raise RuntimeError("Command timed out after {timeout} seconds: stdout['{stdout}'], "
                                   "stderr['{stderr}']".format(timeout=timeout, stdout=stdout, stderr=stderr))
    return stdout, stderr
