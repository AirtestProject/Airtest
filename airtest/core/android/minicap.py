# -*- coding: utf-8 -*-
import os
import re
import json
import struct
import threading
import traceback
from airtest.core.android.constant import STFLIB
from airtest.core.error import AdbShellError
from airtest.utils.compat import PY3
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.safesocket import SafeSocket
from airtest.utils.snippet import reg_cleanup, on_method_ready, ready_method


LOGGING = get_logger(__name__)


class Minicap(object):
    """super fast android screenshot method from stf minicap.

    reference https://github.com/openstf/minicap
    """

    VERSION = 5
    RECVTIMEOUT = None
    CMD = "LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap"

    def __init__(self, adb, projection=None):
        """
        :param adb: adb instance of android device
        :param projection: projection, default is None. If `None`, physical display size is used
        """
        self.adb = adb
        self.projection = projection
        self.frame_gen = None
        self.stream_lock = threading.Lock()
        self.quirk_flag = 0

    @ready_method
    def install_or_upgrade(self):
        """
        Install or upgrade minicap

        Returns:
            None

        """
        if self.adb.exists_file("/data/local/tmp/minicap") \
                and self.adb.exists_file("/data/local/tmp/minicap.so"):
            try:
                output = self.adb.raw_shell("%s -v 2>&1" % self.CMD)
            except Exception as err:
                LOGGING.error(str(err))
                version = -1
            else:
                LOGGING.debug(output.strip())
                m = re.match("version:(\d)", output)
                if m:
                    version = int(m.group(1))
                else:
                    version = -1
            if version >= self.VERSION:
                LOGGING.debug('skip install minicap')
                return
            else:
                LOGGING.debug('upgrade minicap to lastest version: %s->%s' % (version, self.VERSION))
                self.uninstall()
        else:
            LOGGING.debug('install minicap')
        self.install()

    def uninstall(self):
        """
        Uninstall minicap

        Returns:
            None

        """
        self.adb.raw_shell("rm /data/local/tmp/minicap*")

    def install(self):
        """
        Install minicap

        Reference: https://github.com/openstf/minicap/blob/master/run.sh

        Returns:
            None

        """
        abi = self.adb.getprop("ro.product.cpu.abi")
        pre = self.adb.getprop("ro.build.version.preview_sdk")
        rel = self.adb.getprop("ro.build.version.release")
        sdk = self.adb.sdk_version

        if pre.isdigit() and int(pre) > 0:
            sdk += 1

        if sdk >= 16:
            binfile = "minicap"
        else:
            binfile = "minicap-nopie"

        device_dir = "/data/local/tmp"

        path = os.path.join(STFLIB, abi, binfile)
        self.adb.push(path, "%s/minicap" % device_dir)
        self.adb.shell("chmod 755 %s/minicap" % device_dir)

        pattern = os.path.join(STFLIB, 'minicap-shared/aosp/libs/android-%s/%s/minicap.so')
        path = pattern % (sdk, abi)
        if not os.path.isfile(path):
            path = pattern % (rel, abi)

        self.adb.push(path, "%s/minicap.so" % device_dir)
        self.adb.shell("chmod 755 %s/minicap.so" % device_dir)
        LOGGING.info("minicap installation finished")

    @on_method_ready('install_or_upgrade')
    def get_display_info(self):
        """
        Get display info by minicap

        Warnings:
            It might segfault, the preferred way is to get the information from adb commands

        Returns:
            display information

        """
        display_info = self.adb.shell("%s -i" % self.CMD)
        display_info = json.loads(display_info)
        return display_info

    @on_method_ready('install_or_upgrade')
    def get_frame(self, projection=None):
        """
        Get the single frame from minicap -s, this method slower than `get_frames`
            1. shell cmd
            1. remove log info
            1. \r\r\n -> \n ...

        Args:
            projection: screenshot projection, default is None which means using self.projection

        Returns:
            jpg data

        """
        raw_data = self.adb.raw_shell(
            self.CMD + " -n 'airtest_minicap' -P %dx%d@%dx%d/%d -s" %
            self._get_params(projection),
            ensure_unicode=False,
        )
        jpg_data = raw_data.split(b"for JPG encoder" + self.adb.line_breaker)[-1].replace(self.adb.line_breaker, b"\n")
        return jpg_data

    def _get_params(self, projection=None):
        """
        Get the minicap origin parameters and count the projection

        Returns:
            physical display size (width, height), counted projection (width, height) and real display orientation

        """
        # minicap截屏时，需要截取物理全屏的图片:
        real_width = self.adb.display_info["physical_width"]
        real_height = self.adb.display_info["physical_height"]
        real_orientation = self.adb.display_info["rotation"]
        # 优先去传入的projection
        projection = projection or self.projection
        if projection:
            proj_width, proj_height = projection
        else:
            proj_width, proj_height = real_width, real_height

        if self.quirk_flag & 2 and real_orientation != 0:
            return real_height, real_width, proj_height, proj_width, 0

        return real_width, real_height, proj_width, proj_height, real_orientation

    @on_method_ready('install_or_upgrade')
    def get_stream(self, lazy=True):
        """
        Get stream, it uses `adb forward`and socket communication. Use minicap ``lazy``mode (provided by gzmaruijie)
        for long connections - returns one latest frame from the server


        Args:
            lazy: True or False

        Returns:

        """
        gen = self._get_stream(lazy)

        # if quirk error, restart server and client once
        stopped = next(gen)

        if stopped:
            try:
                next(gen)
            except StopIteration:
                pass
            gen = self._get_stream(lazy)
            next(gen)

        return gen

    @on_method_ready('install_or_upgrade')
    def _get_stream(self, lazy=True):
        proc, nbsp, localport = self._setup_stream_server(lazy=lazy)
        s = SafeSocket()
        s.connect((self.adb.host, localport))
        t = s.recv(24)
        # minicap header
        global_headers = struct.unpack("<2B5I2B", t)
        LOGGING.debug(global_headers)
        # check quirk-bitflags, reference: https://github.com/openstf/minicap#quirk-bitflags
        ori, self.quirk_flag = global_headers[-2:]

        if self.quirk_flag & 2 and ori != 0:
            # resetup
            LOGGING.debug("quirk_flag found, going to resetup")
            stopping = True
        else:
            stopping = False
        yield stopping

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
        """
        Setup minicap process on device

        Args:
            lazy: parameter `-l` is used when True

        Returns:
            adb shell process, non-blocking stream reader and local port

        """
        localport, deviceport = self.adb.setup_forward("localabstract:minicap_{}".format)
        deviceport = deviceport[len("localabstract:"):]
        other_opt = "-l" if lazy else ""
        params = self._get_params()
        proc = self.adb.start_shell(
            "%s -n '%s' -P %dx%d@%dx%d/%d %s 2>&1" %
            tuple([self.CMD, deviceport] + list(params) + [other_opt]),
        )
        nbsp = NonBlockingStreamReader(proc.stdout, print_output=True, name="minicap_server")
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
        reg_cleanup(proc.kill)
        return proc, nbsp, localport

    def get_frame_from_stream(self):
        """
        Get one frame from minicap stream

        Returns:
            frame

        """
        with self.stream_lock:
            if self.frame_gen is None:
                self.frame_gen = self.get_stream()
            if not PY3:
                frame = self.frame_gen.next()
            else:
                frame = self.frame_gen.__next__()
            return frame

    def update_rotation(self, rotation):
        """
        Update rotation and reset the backend stream generator

        Args:
            rotation: rotation input

        Returns:
            None

        """
        LOGGING.debug("update_rotation: %s" % rotation)
        self.teardown_stream()

    def teardown_stream(self):
        """
        End the stream

        Returns:
            None

        """
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
