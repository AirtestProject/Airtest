# _*_ coding:UTF-8 _*_
"""
cleanup when process ends
todo: cleanup level
"""
import atexit


def reg_cleanup(func, *args, **kwargs):
    atexit.register(func, *args, **kwargs)
