import sys
from six import PY3

if PY3:
    def decode_path(path):
        return path
else:
    def decode_path(path):
        return path.decode(sys.getfilesystemencoding()) if path else path
