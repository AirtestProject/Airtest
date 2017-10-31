# -*- coding: utf-8 -*-
import json
import os
import struct
import threading

from airtest.core.android.constant import STFLIB
from airtest.core.error import AdbShellError
from airtest.utils.compat import PY3
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.safesocket import SafeSocket
from airtest.utils.snippet import reg_cleanup, on_method_ready

LOGGING = get_logger(__name__)


class Minicap(object):
    """super fast android screenshot method from stf minicap.

    reference https://github.com/openstf/minicap
    """

    VERSION = 4
    RECVTIMEOUT = None
    CMD = "LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap"

    def __init__(self, adb):
        self.adb = adb
        self.frame_gen = None
        self.stream_lock = threading.Lock()
        reg_cleanup(self.teardown_stream)

    def install_or_upgrade(self):
        if self.adb.exists_file("/data/local/tmp/minicap") \
                and self.adb.exists_file("/data/local/tmp/minicap.so"):
            output = self.adb.raw_shell("%s -v 2>&1" % self.CMD)
            try:
                version = int(output.split(":")[1])
            except (ValueError, IndexError):
                version = -1
            if version >= self.VERSION:
                LOGGING.debug('skip install minicap')
                return
            else:
                LOGGING.debug(output)
                LOGGING.debug('upgrade minicap to lastest version:%s', self.VERSION)
        else:
            LOGGING.debug('install minicap')
        self.uninstall()
        self.install()

    def uninstall(self):
        self.adb.raw_shell("rm /data/local/tmp/minicap*")

    def install(self):
        """install or upgrade minicap"""
        abi = self.adb.getprop("ro.product.cpu.abi")
        if self.adb.sdk_version >= 16:
            binfile = "minicap"
        else:
            binfile = "minicap-nopie"

        device_dir = "/data/local/tmp"
        path = os.path.join(STFLIB, abi, binfile).replace("\\", r"\\")
        self.adb.cmd("push %s %s/minicap" % (path, device_dir))
        self.adb.shell("chmod 755 %s/minicap" % device_dir)

        path = os.path.join(STFLIB, 'minicap-shared/aosp/libs/android-%d/%s/minicap.so' %
                            (self.adb.sdk_version, abi)).replace("\\", r"\\")
        self.adb.cmd("push %s %s" % (path, device_dir))
        self.adb.shell("chmod 755 %s/minicap.so" % device_dir)
        LOGGING.info("minicap installation finished")

    @on_method_ready('install_or_upgrade')
    def get_display_info(self):
        """
        get display info by minicap
        warning: it may segfault, so we prefer to get from adb
        """
        display_info = self.adb.shell("%s -i" % self.CMD)
        display_info = json.loads(display_info)
        return display_info

    @on_method_ready('install_or_upgrade')
    def get_frame(self, projection=None):
        """
        get single frame from minicap -s, slower than get_frames
        1. shell cmd
        2. remove log info
        3. \r\r\n -> \n ... fuck adb
        """
        raw_data = self.adb.raw_shell(
            self.CMD + " -n 'airtest_minicap' -P %dx%d@%dx%d/%d -s" %
            self._get_params(projection),
            ensure_unicode=False,
        )
        jpg_data = raw_data.split(b"for JPG encoder" + self.adb.line_breaker)[-1].replace(self.adb.line_breaker, b"\n")
        return jpg_data

    def _get_params(self, projection=None):
        """get minicap start params, and count projection"""
        # minicap截屏时，需要截取物理全屏的图片:
        real_width = self.adb.display_info["physical_width"]
        real_height = self.adb.display_info["physical_height"]
        real_orientation = self.adb.display_info["rotation"]
        if projection:
            proj_width, proj_height = projection
        else:
            proj_width, proj_height = real_width, real_height
        return real_width, real_height, proj_width, proj_height, real_orientation

    @on_method_ready('install_or_upgrade')
    def get_stream(self, lazy=True):
        """
        Use adb forward and socket communicate.

        lazy: use minicap lazy mode (provided by gzmaruijie)
              long connection, send 1 to server, than server return one lastest frame
        """
        proc, nbsp, localport = self._setup_stream_server(lazy=lazy)
        s = SafeSocket()
        s.connect((self.adb.host, localport))
        t = s.recv(24)
        # minicap header
        LOGGING.debug(struct.unpack("<2B5I2B", t))

        stopping = False
        while not stopping:
            if lazy:
                s.send(b"1")
            # recv frame header, count frame_size
            if self.RECVTIMEOUT is not None:
                header = s.recv_with_timeout(4, self.RECVTIMEOUT)
            else:
                header = s.recv(4)
            if header is None:
                LOGGING.error("minicap header is None")
                # recv timeout, if not frame updated, maybe screen locked
                stopping = yield None
            else:
                frame_size = struct.unpack("<I", header)[0]
                frame_data = s.recv(frame_size)
                stopping = yield frame_data

        LOGGING.debug("minicap stream ends")
        s.close()
        nbsp.kill()
        proc.kill()
        self.adb.remove_forward("tcp:%s" % localport)

    def _setup_stream_server(self, lazy=False):
        """setup minicap process on device"""
        localport, deviceport = self.adb.setup_forward("localabstract:minicap_{}".format)
        deviceport = deviceport[len("localabstract:"):]
        other_opt = "-l" if lazy else ""
        params = self._get_params()
        proc = self.adb.start_shell(
            "%s -n '%s' -P %dx%d@%dx%d/%d %s 2>&1" %
            tuple([self.CMD, deviceport] + list(params) + [other_opt]),
        )
        nbsp = NonBlockingStreamReader(proc.stdout, print_output=True, name="minicap_sever")
        while True:
            line = nbsp.readline(timeout=5.0)
            if line is None:
                raise RuntimeError("minicap server setup timeout")
            if b"Server start" in line:
                break

        if proc.poll() is not None:
            # minicap server setup error, may be already setup by others
            # subprocess exit immediately
            raise RuntimeError("minicap server quit immediately")
        return proc, nbsp, localport

    def get_frame_from_stream(self):
        """get one frame from minicap stream"""
        with self.stream_lock:
            if self.frame_gen is None:
                self.frame_gen = self.get_stream()
            if not PY3:
                frame = self.frame_gen.next()
            else:
                frame = self.frame_gen.__next__()
            return frame

    def update_rotation(self, rotation):
        """update rotation, and reset backend stream generator"""
        LOGGING.debug("update_rotation: %s" % rotation)
        self.teardown_stream()

    def teardown_stream(self):
        with self.stream_lock:
            if not self.frame_gen:
                return
            try:
                self.frame_gen.send(1)
            except (TypeError, StopIteration):
                # TypeError: can't send non-None value to a just-started generator
                pass
            else:
                LOGGING.warn("%s tear down failed" % self.frame_gen)
            self.frame_gen = None

