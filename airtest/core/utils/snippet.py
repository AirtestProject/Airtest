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


def get_std_encoding(stream):
    return getattr(stream, "encoding", None) or sys.getfilesystemencoding()
