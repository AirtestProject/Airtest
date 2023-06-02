"""
This package provide IOS Device Class.
"""
import six
if six.PY2:
    raise ImportError(
        "The iOS module of Airtest>1.1.7 only supports Python3, if you want to use, please upgrade to Python3 first.")
from airtest.core.ios.ios import IOS, TIDevice
