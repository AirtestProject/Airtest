# _*_ coding:UTF-8 _*_


def split_cmd(cmds):
    """split cmd to list, for subprocess"""
    if isinstance(cmds, basestring):
        # cmds = shlex.split(cmds)  # disable auto removing \ on windows
        cmds = cmds.split()
    else:
        cmds = list(cmds)
    return cmds

def is_str(s):
    return isinstance(s, basestring)

def is_list(v):
    return isinstance(v, list) or isinstance(v, tuple)
