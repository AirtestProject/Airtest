# -*- coding: utf-8 -*-
from airtest.core.android.adb import ADB
from airtest.core.error import AdbShellError, MinicapError
from airtest.core.android.constant import STFLIB
from airtest.core.utils import SafeSocket, NonBlockingStreamReader, reg_cleanup, retries, get_logger
from airtest.core.utils.compat import PY3
import threading
import struct
import json
import sys
import os
LOGGING = get_logger('minicap')


class Minicap(object):

    """quick screenshot from minicap  https://github.com/openstf/minicap"""

    VERSION = 4
    CAPTIMEOUT = None

    def __init__(self, serialno, projection=1, localport=None, adb=None, stream=True):
        self.serialno = serialno
        self.localport = localport
        self.server_proc = None
        self.projection = projection
        self.adb = adb or ADB(serialno)
        self.install()
        self._display_info = None
        self.current_rotation = None
        self.stream_mode = stream
        self.frame_gen = None
        self.stream_lock = threading.Lock()
        self.quirk_flag = 0

    def install(self, reinstall=False):
        """install or upgrade minicap"""
        # reinstall = True
        if not reinstall and self.adb.exists_file("/data/local/tmp/minicap") \
                and self.adb.exists_file("/data/local/tmp/minicap.so"):
            output = self.adb.shell("LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -v 2>&1")
            try:
                version = int(output.split(":")[1])
            except (ValueError, IndexError):
                version = -1
            if version >= self.VERSION:
                LOGGING.debug('minicap install skipped')
                return
            else:
                LOGGING.debug(output)
                LOGGING.debug('upgrading minicap to lastest version:%s', self.VERSION)
        try:
            self.adb.shell("rm /data/local/tmp/minicap*")
        except AdbShellError:
            pass
        abi = self.adb.getprop("ro.product.cpu.abi")
        sdk = int(self.adb.getprop("ro.build.version.sdk"))
        rel = self.adb.getprop("ro.build.version.release")
        if sdk >= 16:
            binfile = "minicap"
        else:
            binfile = "minicap-nopie"

        device_dir = "/data/local/tmp"
        path = os.path.join(STFLIB, abi, binfile).replace("\\", r"\\")
        self.adb.cmd("push %s %s/minicap" % (path, device_dir))
        self.adb.shell("chmod 755 %s/minicap" % (device_dir))

        path = os.path.join(STFLIB, 'minicap-shared/aosp/libs/android-%d/%s/minicap.so' % (sdk, abi)).replace("\\", r"\\")
        self.adb.cmd("push %s %s" % (path, device_dir))
        self.adb.shell("chmod 755 %s/minicap.so" % (device_dir))
        LOGGING.info("minicap install finished")

    @property
    def display_info(self):
        if not self._display_info:
            # get_display_info may segfault, so use size info from adb dumpsys
            self._display_info = self.adb.display_info or self.get_display_info()
        return self._display_info

    def _get_params(self, use_ori_size=False):
        """get minicap start params, and count projection"""
        # minicap截屏时，需要截取全屏图片:
        real_width = self.display_info["physical_width"]
        real_height = self.display_info["physical_height"]
        real_orientation = self.display_info["rotation"]

        if use_ori_size or not self.projection:
            proj_width, proj_height = real_width, real_height
        elif isinstance(self.projection, (list, tuple)):
            proj_width, proj_height = self.projection
        elif isinstance(self.projection, (int, float)):
            proj_width = self.projection * real_width
            proj_height = self.projection * real_height
        else:
            raise RuntimeError("invalid projection type: %s" % repr(self.projection))
        if self.quirk_flag & 2 and real_orientation != 0:
            return real_height, real_width, proj_height, proj_width, 0, real_orientation
        return real_width, real_height, proj_width, proj_height, real_orientation, real_orientation

    def _setup(self, adb_port=None, lazy=False):
        """setup minicap process on device"""
        # 可能需要改变参数重新setup，所以之前setup过的先关掉
        if self.server_proc:
            LOGGING.debug("****************resetup****************")
            sys.stdout.flush()
            self.server_proc.kill()
            self.nbsp.kill()
            self.server_proc = None
            self.adb.remove_forward("tcp:%s" % self.localport)

        real_width, real_height, proj_width, proj_height, minicap_orientation, real_orientation = self._get_params()

        self.localport, deviceport = self.adb.setup_forward("localabstract:minicap_{}".format)
        deviceport = deviceport[len("localabstract:"):]
        other_opt = "-l" if lazy else ""
        proc = self.adb.shell(
            "LD_LIBRARY_PATH=/data/local/tmp/ /data/local/tmp/minicap -n '%s' -P %dx%d@%dx%d/%d %s 2>&1" % (
                deviceport,
                real_width, real_height,
                proj_width, proj_height,
                minicap_orientation, other_opt),
            not_wait=True
        )
        nbsp = NonBlockingStreamReader(proc.stdout, print_output=True, name="minicap_sever")
        while True:
            line = nbsp.readline(timeout=5.0)
            if line is None:
                raise RuntimeError("minicap setup error")
            if b"Server start" in line:
                break

        if proc.poll() is not None:
            # minicap server setup error, may be already setup by others
            # subprocess exit immediately
            raise RuntimeError("minicap setup error")
        reg_cleanup(proc.kill)
        self.server_proc = proc
        self.current_rotation = real_orientation
        self.nbsp = nbsp

    def get_display_info(self):
        """
        get display info by minicap
        warning: it may segfault, so we prefer to get from adb
        """
        display_info = self.adb.shell("LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -i")
        display_info = json.loads(display_info)
        if display_info['width'] > display_info['height'] and display_info['rotation'] in [90, 270]:
            display_info['width'], display_info['height'] = display_info['height'], display_info['width']
        self.display_info = display_info
        return display_info

    def get_frame(self, use_ori_size=True):
        """
        get single frame from minicap -s, slower than get_frames
        1. shell cmd
        2. remove log info
        3. \r\r\n -> \n ... fuck adb
        """
        real_width, real_height, proj_width, proj_height, real_orientation, _ = self._get_params(use_ori_size)

        raw_data = self.adb.cmd(
            "shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -n 'moa_minicap' -P %dx%d@%dx%d/%d -s" %
            (real_width, real_height, proj_width, proj_height, real_orientation),
            not_decode=True,
        )

        jpg_data = raw_data.split(b"for JPG encoder" + self.adb.line_breaker)[-1].replace(self.adb.line_breaker, b"\n")
        return jpg_data

    def get_frames(self, max_cnt=1000000000, adb_port=None, lazy=False):
        """
        use adb forward and socket communicate
        lazy: use minicap lazy mode (provided by gzmaruijie)
              long connection, send 1 to server, than server return one lastest frame
        """
        self._setup(adb_port, lazy=lazy)
        s = SafeSocket()
        port = adb_port or self.localport
        s.connect((self.adb.host, port))
        t = s.recv(24)
        # minicap info
        global_headers = struct.unpack("<2B5I2B", t)
        LOGGING.debug(global_headers)
        ori, self.quirk_flag = global_headers[-2:]
        if self.quirk_flag & 2 and ori != 0:
            self._setup(adb_port, lazy=lazy)
            s.close()
            s = SafeSocket()
            _port = adb_port or self.localport
            s.connect((self.adb.host, _port))
            t = s.recv(24)
            # minicap info
            global_headers = struct.unpack("<2B5I2B", t)
            ori, self.quirk_flag = global_headers[-2:]
            LOGGING.debug(global_headers)

        yield global_headers

        cnt = 0
        while cnt <= max_cnt:
            if lazy:
                s.send(b"1")
            cnt += 1
            # recv header, count frame_size
            if self.CAPTIMEOUT is not None:
                header = s.recv_with_timeout(4, self.CAPTIMEOUT)
            else:
                header = s.recv(4)
            if header is None:
                LOGGING.error("minicap header is None")
                # recv timeout, if not frame updated, maybe screen locked
                yield None
            else:
                frame_size = struct.unpack("<I", header)[0]
                # recv image data
                one_frame = s.recv(frame_size)
                yield one_frame
        s.close()

    def get_header(self):
        """get minicap header info"""
        pass

    def init_stream(self):
        """init minicap stream and set stream_mode"""
        self.stream_mode = True
        self.frame_gen = self.get_frames(lazy=True)
        if not PY3:
            LOGGING.debug("minicap header: %s", str(self.frame_gen.next()))
        else:
            # for py 3
            LOGGING.debug("minicap header: %s", str(self.frame_gen.__next__()))

    def get_frame_from_stream(self):
        """get one frame from minicap stream"""
        with self.stream_lock:
            if self.frame_gen is None:
                self.init_stream()
            if not PY3:
                frame = self.frame_gen.next()
            else:
                frame = self.frame_gen.__next__()
            return frame

    def update_rotation(self, rotation):
        """update rotation, and reset backend stream generator"""
        print("%s -> %s" % (self.current_rotation, rotation))
        with self.stream_lock:
            self.display_info["rotation"] = rotation
            if str(rotation) == str(self.current_rotation):
                LOGGING.debug("update_rotation is the same with current_rotation %s" % rotation)
            else:
                self.frame_gen = None
