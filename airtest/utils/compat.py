import sys
import os
from six import PY3, raise_from, reraise


EXT = ".air"  # script dir extension
DEFAULT_LOG_DIR = "log"  # <script_dir>/log


if PY3:
    def decode_path(path):
        return path
else:
    def decode_path(path):
        return path.decode(sys.getfilesystemencoding()) if path else path


def script_dir_name(script_path):
    """get script dir for old & new cli api compatibility"""
    script_path = decode_path(script_path)
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