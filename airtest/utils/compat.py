import sys
import os
from six import PY3

if PY3:
    def decode_path(path):
        return path
else:
    def decode_path(path):
        return path.decode(sys.getfilesystemencoding()) if path else path


def script_dir(script_path):
    """get script dir for old & new cli api compatibility"""
    if script_path.endswith(".air"):
        path = decode_path(script_path)
    else:
        path = os.path.dirname(script_path) or "."
    return path
