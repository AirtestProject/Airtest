# -*- coding: utf-8 -*-
import os
import re
import json
import struct
import threading
import six
import socket
from functools import wraps
from airtest.core.android.constant import STFLIB, ORI_METHOD
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.safesocket import SafeSocket
from airtest.utils.snippet import reg_cleanup, on_method_ready, ready_method


LOGGING = get_logger(__name__)


def retry_when_socket_error(func):
    @wraps(func)
    def wrapper(inst, *args, **kwargs):
        try:
            return func(inst, *args, **kwargs)
        except socket.error:
            inst.frame_gen = None
            return func(inst, *args, **kwargs)
    return wrapper


class Minicap(object):
    """super fast android screenshot method from stf minicap.

    reference https://github.com/openstf/minicap
    """

    VERSION = 5
    RECVTIMEOUT = None
    CMD = "LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap"

    def __init__(self, adb, projection=None, ori_function=None):
        """
        :param adb: adb instance of android device
        :param projection: projection, default is None. If `None`, physical display size is used
        """
        self.adb = adb
        self.projection = projection
        self.ori_function = ori_function if callable(ori_function) else self.get_display_info
        self.frame_gen = None
        self.stream_lock = threading.Lock()
        self.quirk_flag = 0
        self._stream_rotation = None
        self._update_rotation_event = threading.Event()

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
        display_info["orientation"] = display_info["rotation"] / 90
        # 针对调整过手机分辨率的情况
        actual = self.adb.shell("dumpsys window displays")
        arr = re.findall(r'cur=(\d+)x(\d+)', actual)
        if len(arr) > 0:
            display_info['physical_width'] = display_info['width']
            display_info['physical_height'] = display_info['height']
            # 通过 adb shell dumpsys window displays | find "cur="
            # 获取到的分辨率是实际分辨率，但是需要的是非实际的
            if display_info["orientation"] in [1, 3]:
                display_info['width'] = int(arr[0][1])
                display_info['height'] = int(arr[0][0])
            else:
                display_info['width'] = int(arr[0][0])
                display_info['height'] = int(arr[0][1])
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
        params, display_info = self._get_params(projection)
        raw_data = self.adb.raw_shell(
            self.CMD + " -n 'airtest_minicap' -P %dx%d@%dx%d/%d -s" % params,
            ensure_unicode=False,
        )
        jpg_data = raw_data.split(b"for JPG encoder" + self.adb.line_breaker)[-1]
        jpg_data = jpg_data.replace(self.adb.line_breaker, b"\n")
        return jpg_data

    def _get_params(self, projection=None):
        """
        Get the minicap origin parameters and count the projection

        Returns:
            physical display size (width, height), counted projection (width, height) and real display orientation

        """
        display_info = self.ori_function()
        real_width = display_info["width"]
        real_height = display_info["height"]
        real_rotation = display_info["rotation"]
        # 优先去传入的projection
        projection = projection or self.projection
        if projection:
            proj_width, proj_height = projection
        else:
            proj_width, proj_height = real_width, real_height

        if self.quirk_flag & 2 and real_rotation in (90, 270):
            params = real_height, real_width, proj_height, proj_width, 0
        else:
            params = real_width, real_height, proj_width, proj_height, real_rotation

        return (params, display_info)

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

        if self.quirk_flag & 2 and ori in (1, 3):
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
        self.adb.close_proc_pipe(proc)

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
        params, display_info = self._get_params()
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
        self._stream_rotation = int(display_info["rotation"])
        return proc, nbsp, localport

    @retry_when_socket_error
    def get_frame_from_stream(self):
        """
        Get one frame from minicap stream

        Returns:
            frame

        """
        if self._update_rotation_event.is_set():
            LOGGING.debug("do update rotation")
            self.teardown_stream()
            self._update_rotation_event.clear()
        if self.frame_gen is None:
            self.frame_gen = self.get_stream()
        return six.next(self.frame_gen)

    def update_rotation(self, rotation):
        """
        Update rotation and reset the backend stream generator

        Args:
            rotation: rotation input

        Returns:
            None

        """
        LOGGING.debug("update_rotation: %s" % rotation)
        self._update_rotation_event.set()

    def teardown_stream(self):
        """
        End the stream

        Returns:
            None

        """
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


