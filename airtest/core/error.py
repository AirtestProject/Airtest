# -*- coding: utf-8 -*-

"""
error classes
"""

class BaseError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class AirtestError(BaseError):
    """
        This is Airtest BaseError
    """
    pass


class TargetNotFoundError(AirtestError):
    """
        This is TargetNotFoundError BaseError
        When something is not found
    """
    pass


class ScriptParamError(AirtestError):
    """
        This is ScriptParamError BaseError
        When something goes wrong
    """
    pass


class AdbError(Exception):
    """
        This is AdbError BaseError
        When ADB have something wrong
    """
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return "stdout[%s] stderr[%s]" % (self.stdout, self.stderr)


class AdbShellError(AdbError):
    """
        adb shell error
    """
    pass


class DeviceConnectionError(BaseError):
    """
        device connection error
    """
    DEVICE_CONNECTION_ERROR = r"error:\s*((device \'\w+\' not found)|(cannot connect to daemon at [\w\:\s\.]+ Connection timed out))"
    pass


class ICmdError(Exception):
    """
        This is ICmdError BaseError
        When ICmd have something wrong
    """    
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return "stdout[%s] stderr[%s]" %(self.stdout, self.stderr)


class MinicapError(BaseError):
    """
        This is MinicapError BaseError
        When Minicap have something wrong
    """    
    pass


class MinitouchError(BaseError):
    """
        This is MinitouchError BaseError
        When Minicap have something wrong
    """    
    pass


class PerformanceError(BaseError):
    pass