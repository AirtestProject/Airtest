# _*_ coding:UTF-8 _*_
import os
import sys
import stat
import threading
from functools import wraps
from six import string_types
from six.moves import queue


def split_cmd(cmds):
    """
    Split the commands to the list for subprocess

    Args:
        cmds: command(s)

    Returns:
        array commands

    """
    # cmds = shlex.split(cmds)  # disable auto removing \ on windows
    return cmds.split() if isinstance(cmds, string_types) else list(cmds)


def get_std_encoding(stream):
    """
    Get encoding of the stream

    Args:
        stream: stream

    Returns:
        encoding or file system encoding

    """
    return getattr(stream, "encoding", None) or sys.getfilesystemencoding()


CLEANUP_CALLS = queue.Queue()
IS_EXITING = False


def reg_cleanup(func, *args, **kwargs):
    """
    Clean the register for given function

    Args:
        func: function name
        *args: optional argument
        **kwargs: optional arguments

    Returns:
        None

    """
    CLEANUP_CALLS.put((func, args, kwargs))


def _cleanup():
    # cleanup together to prevent atexit thread issue
    while not CLEANUP_CALLS.empty():
        (func, args, kwargs) = CLEANUP_CALLS.get()
        func(*args, **kwargs)


def kill_proc(proc):
    """
    Kill the process and close _io.BufferedWriter to avoid `ResourceWarning: unclosed file <_io.BufferedWriter name=6>`

    Args:
        proc: subprocess.Popen()

    Returns:

    """
    proc.kill()
    # https://bugs.python.org/issue35182
    # 部分低版本的python中，重复关闭io流可能会导致异常报错，因此需要额外加入判断closed
    if proc.stdout and not proc.stdout.closed:
        proc.communicate()


# atexit.register(_cleanup)

_shutdown = threading._shutdown


def exitfunc():
    global IS_EXITING
    IS_EXITING = True
    _cleanup()
    _shutdown()


def is_exiting():
    return IS_EXITING


# use threading._shutdown to exec cleanup when main thread exit
# atexit exec after all thread exit, which needs to cooperate with daemon thread.
# daemon thread is evil, which abruptly exit causing unexpected error
threading._shutdown = exitfunc


def on_method_ready(method_name):
    """
    Wrapper for lazy initialization of some instance methods

    Args:
        method_name: instance method name

    Returns:
        wrapper

    """
    def wrapper(func):
        @wraps(func)
        def ready_func(inst, *args, **kwargs):
            key = "_%s_ready" % method_name
            if not getattr(inst, key, None):
                method = getattr(inst, method_name)
                method()
                setattr(inst, key, True)
            return func(inst, *args, **kwargs)
        return ready_func
    return wrapper


def ready_method(func):
    @wraps(func)
    def wrapper(inst, *args, **kwargs):
        ret = func(inst, *args, **kwargs)
        key = "_%s_ready" % func.__name__
        if not getattr(inst, key, None):
            setattr(inst, key, True)
        return ret
    return wrapper


def make_file_executable(file_path):
    """
    If the path does not have executable permissions, execute chmod +x
    :param file_path:
    :return:
    """
    if os.path.isfile(file_path):
        mode = os.lstat(file_path)[stat.ST_MODE]
        executable = True if mode & stat.S_IXUSR else False
        if not executable:
            os.chmod(file_path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return True
    return False
