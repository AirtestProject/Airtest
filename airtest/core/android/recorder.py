# -*- coding: utf-8 -*-
import re
import time

import six
from airtest.core.android.yosemite import Yosemite
from airtest.core.android.constant import YOSEMITE_PACKAGE
from airtest.core.error import AirtestError
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.snippet import on_method_ready
LOGGING = get_logger(__name__)


class Recorder(Yosemite):
    """Screen recorder"""

    def __init__(self, adb):
        super(Recorder, self).__init__(adb)
        self.recording_proc = None
        self.recording_file = None

    @on_method_ready('install_or_upgrade')
    def start_recording(self, max_time=1800, bit_rate=None, vertical=None):
        """
        Start screen recording

        Args:
            max_time: maximum rate value, default is 1800
            bit_rate: bit rate value, default is None
            vertical: vertical parameters, default is None

        Raises:
            RuntimeError: if any error occurs while setup the recording

        Returns:
            None if recording did not start, otherwise True

        """
        p = self.adb.start_shell('am broadcast -a YOSEMITE_SCREENRECORD_START')
        return True

    @on_method_ready('install_or_upgrade')
    def stop_recording(self, output="screen.mp4", is_interrupted=False):
        """
        Stop screen recording

        Args:
            output: default file is `screen.mp4`
            is_interrupted: True or False. Stop only, no pulling recorded file from device.

        Raises:
            AirtestError: if recording was not started before

        Returns:
            None

        """
        p = self.adb.start_shell('am broadcast -a YOSEMITE_SCREENRECORD_STOP ')
        time.sleep(5)
        self.adb.pull('mnt/sdcard/' + self.adb.get_model() + '_test.mp4', output)
        return True

    @on_method_ready('install_or_upgrade')
    def pull_last_recording_file(self, output='screen.mp4'):
        """
        Pull the latest recording file from device. Error raises if no recording files on device.

        Args:
            output: default file is `screen.mp4`

        """
        recording_file = 'mnt/sdcard/test.mp4'
        self.adb.pull(recording_file, output)
