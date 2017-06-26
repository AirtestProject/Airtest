# _*_ coding:UTF-8 _*_
from airtest.core.utils.compat import str_class
import sys


def split_cmd(cmds):
    """split cmd to list, for subprocess"""
    if isinstance(cmds, str_class):
        # cmds = shlex.split(cmds)  # disable auto removing \ on windows
        cmds = cmds.split()
    else:
        cmds = list(cmds)
    return cmds


def is_str(s):
    return isinstance(s, str_class)


def is_list(v):
    return isinstance(v, list) or isinstance(v, tuple)


def get_std_encoding(stream):
    return getattr(stream, "encoding", None) or sys.getfilesystemencoding()