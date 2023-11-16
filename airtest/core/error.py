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


class InvalidMatchingMethodError(BaseError):
    """
        This is InvalidMatchingMethodError BaseError
        When an invalid matching method is used in settings.
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
    DEVICE_CONNECTION_ERROR = r"error:\s*((device \'\S+\' not found)|(cannot connect to daemon at [\w\:\s\.]+ Connection timed out))"
    pass

class NoDeviceError(BaseError):
    """
        When no device is connected
    """
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


class ScreenError(BaseError):
    """
    When the screen capture method(Minicap/Javacap/ScreenProxy) has something wrong
    """
    pass


class MinicapError(ScreenError):
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


class LocalDeviceError(BaseError):
    """
    Custom exception for calling a method on a non-local iOS device.
    """
    def __init__(self, value="Can only use this method on a local device."):
        super().__init__(value)
