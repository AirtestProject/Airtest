# _*_ coding:UTF-8 _*_
import atexit
import sys
from functools import wraps
from .compat import str_class, queue


def split_cmd(cmds):
    """
    Split the commands to the list for subprocess

    Args:
        cmds: command(s)

    Returns:
        array commands

    """
    if isinstance(cmds, str_class):
        # cmds = shlex.split(cmds)  # disable auto removing \ on windows
        cmds = cmds.split()
    else:
        cmds = list(cmds)
    return cmds


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
    # atexit.register(func, *args, **kwargs)


def _cleanup():
    # cleanup together to prevent atexit thread issue
    while not CLEANUP_CALLS.empty():
        (func, args, kwargs) = CLEANUP_CALLS.get()
        func(*args, **kwargs)


# atexit.register(_cleanup)

import threading


_shutdown = threading._shutdown


def exitfunc():
    print("exiting.......")
    _cleanup()
    _shutdown()


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
        key = "_%s_ready" % func.__name__
        ret = func(inst, *args, **kwargs)
        setattr(inst, key, True)
        return ret
    return wrapper
