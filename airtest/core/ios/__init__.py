"""
This package provide IOS Device Class.
"""
import six
if six.PY2:
    raise ImportError(
        "The iOS module of Airtest>1.1.7 only supports Python3, if you want to use, please upgrade to Python3 first.")
from airtest.core.ios.ios import IOS
from airtest.core.ios.tidevice_helper import TIDevice
from airtest.core.ios.goios_helper import GOIOSHelper
from airtest.core.ios.ios_utils import (
    ios_launch_wda, ios_run_xctest, ios_list_devices, ios_list_wda, ios_get_device_info, ios_get_major_version,
    ios_install_app, ios_uninstall_app, ios_list_app,
    ios_start_app, ios_stop_app, ios_list_processes, ios_list_processes_wda,
    ios_push, ios_pull, ios_rm, ios_ls, ios_mkdir, ios_is_dir
)