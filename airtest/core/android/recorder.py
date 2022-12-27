# -*- coding: utf-8 -*-
import re
import six
from airtest.core.android.yosemite import Yosemite
from airtest.core.android.constant import YOSEMITE_PACKAGE
from airtest.core.error import AirtestError
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.retry import retries
from airtest.utils.snippet import on_method_ready, kill_proc, reg_cleanup
LOGGING = get_logger(__name__)


class Recorder(Yosemite):
    """Screen recorder"""

    def __init__(self, adb):
        super(Recorder, self).__init__(adb)
        self.recording_proc = None
        self.recording_file = None

    @on_method_ready('install_or_upgrade')
    @retries(max_tries=2)
    def start_recording(self, max_time=1800, bit_rate=None, bool_is_vertical="off"):
        """
        Start screen recording

        Args:
            max_time: maximum screen recording time, default is 1800
            bit_rate: bit rate value, 450000-8000000, default is None(6000000)

        Raises:
            RuntimeError: if any error occurs while setup the recording

        Returns:
            None if recording did not start, otherwise True

        """
        if getattr(self, "recording_proc", None):
            raise AirtestError("recording_proc has already started")
        pkg_path = self.adb.path_app(YOSEMITE_PACKAGE)
        max_time_param = "-Dduration=%d" % max_time if max_time else ""
        # The higher the bitrate, the clearer the video, the default value is 6000000
        bit_rate_param = "-Dbitrate=%d" % bit_rate if bit_rate else ""
        bool_is_vertical_param = "-Dvertical=%s" % bool_is_vertical
        # The video size is square, compatible with horizontal and vertical screens
        p = self.adb.start_shell('CLASSPATH=%s exec app_process %s %s %s /system/bin %s.Recorder --start-record' %
                                 (pkg_path, max_time_param, bit_rate_param, bool_is_vertical_param, YOSEMITE_PACKAGE))
        nbsp = NonBlockingStreamReader(p.stdout, name="start_recording_" + str(id(self)))
        # 进程p必须要保留到stop_recording执行时、或是退出前才进行清理，否则会导致录屏进程提前终止
        reg_cleanup(kill_proc, p)
        while True:
            line = nbsp.readline(timeout=5)
            if line is None:
                nbsp.kill()
                kill_proc(p)
                raise RuntimeError("start recording error")
            if six.PY3:
                line = line.decode("utf-8")
            # 如果上次录屏被强制中断，可能会导致无法开始下一次录屏，额外发一个停止录屏指令
            if re.search("Record has already started", line):
                self.stop_recording(is_interrupted=True)
                continue
            m = re.match("start result: Record start success! File path:(.*\.mp4)", line.strip())
            if m:
                output = m.group(1)
                self.recording_proc = p
                self.recording_file = output
                nbsp.kill()
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
        pkg_path = self.adb.path_app(YOSEMITE_PACKAGE)
        p = self.adb.start_shell('CLASSPATH=%s exec app_process /system/bin %s.Recorder --stop-record' % (pkg_path, YOSEMITE_PACKAGE))
        p.wait()
        if self.recording_proc:
            kill_proc(self.recording_proc)
            self.recording_proc = None
        if is_interrupted:
            kill_proc(p)
            return
        for line in p.stdout.readlines():
            if line is None:
                break
            if six.PY3:
                line = line.decode("utf-8")
            m = re.match("stop result: Stop ok! File path:(.*\.mp4)", line.strip())
            if m:
                self.recording_file = m.group(1)
                kill_proc(p)
                self.adb.pull(self.recording_file, output)
                return True
        kill_proc(p)
        raise AirtestError("start_recording first")

    def pull_last_recording_file(self, output='screen.mp4'):
        """
        Pull the latest recording file from device. Error raises if no recording files on device.

        Args:
            output: default file is `screen.mp4`

        """
        recording_file = self.recording_file or 'mnt/sdcard/test.mp4'
        self.adb.pull(recording_file, output)
