# -*- coding: utf-8 -*-

"""
error classes
"""

class BaseError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class MoaError(BaseError):
    pass


class MoaNotFoundError(MoaError):
    pass


class MoaScriptParamError(MoaError):
    pass


class AdbError(Exception):
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return "stdout[%s] stderr[%s]" % (self.stdout, self.stderr)

class ICmdError(Exception):
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return "stdout[%s] stderr[%s]" %(self.stdout, self.stderr)


class MinicapError(BaseError):
    pass

class MinitouchError(BaseError):
    pass
