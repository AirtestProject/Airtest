# coding=utf-8
from airtest.core.android import Android
try:
    from airtest.core.win import Windows
except ImportError:
    Windows = None
try:
    from airtest.core.ios import IOS
except ImportError:
    IOS = None
