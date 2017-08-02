# -*- coding: utf-8 -*-
from airtest.core.android.adb import ADB
from airtest.core.error import AdbShellError, MinicapError
from airtest.core.android.constant import PROJECTIONRATE, STFLIB, MINICAPTIMEOUT
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

    def __init__(self, serialno, size=None, projection=PROJECTIONRATE, localport=None, adb=None, stream=True):
        self.serialno = serialno
        self.localport = localport
        self.server_proc = None
        self.projection = projection
        self.adb = adb or ADB(serialno)
        # get_display_info may segfault, so use size info from adb dumpsys
        self.size = size or self.get_display_info()
        self.install()
        self.stream_mode = stream
        self.frame_gen = None
        self.stream_lock = threading.Lock()

    def install(self, reinstall=False):
        """install or upgrade minicap"""
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

    def _get_params(self, use_ori_size=False):
        """get minicap start params, and count projection"""
        # minicap截屏时，需要截取全屏图片:
        real_width = self.size["physical_width"]
        real_height = self.size["physical_height"]
        real_orientation = self.size["rotation"]

        if use_ori_size or not self.projection:
            proj_width, proj_height = real_width, real_height
        elif isinstance(self.projection, (list, tuple)):
            proj_width, proj_height = self.projection
        elif isinstance(self.projection, (int, float)):
            proj_width = self.projection * real_width
            proj_height = self.projection * real_height
        else:
            raise RuntimeError("invalid projection type: %s" % repr(self.projection))
        return real_width, real_height, proj_width, proj_height, real_orientation

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

        real_width, real_height, proj_width, proj_height, real_orientation = self._get_params()

        @retries(3)
        def set_up_forward():
            localport = adb_port or self.localport or self.adb.get_available_forward_local()
            # localport = 11154
            device_port = "moa_minicap_%s" % localport
            self.adb.forward("tcp:%s" % localport, "localabstract:%s" % device_port)
            return localport, device_port

        self.localport, device_port = set_up_forward()
        other_opt = "-l" if lazy else ""
        proc = self.adb.shell(
            "LD_LIBRARY_PATH=/data/local/tmp/ /data/local/tmp/minicap -n '%s' -P %dx%d@%dx%d/%d %s 2>&1" % (
                device_port,
                real_width, real_height,
                proj_width, proj_height,
                real_orientation, other_opt),
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
        self.size = display_info
        return display_info

    def get_frame(self, use_ori_size=True):
        """
        get single frame from minicap -s, slower than get_frames
        1. shell cmd
        2. remove log info
        3. \r\r\n -> \n ... fuck adb
        """
        real_width, real_height, proj_width, proj_height, real_orientation = self._get_params(use_ori_size)

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
        adb_port = adb_port or self.localport
        s.connect(("localhost", adb_port))
        t = s.recv(24)
        # minicap info
        yield struct.unpack("<2B5I2B", t)

        cnt = 0
        while cnt <= max_cnt:
            if lazy:
                s.send(b"1")
            cnt += 1
            # recv header, count frame_size
            if MINICAPTIMEOUT is not None:
                header = s.recv_with_timeout(4, MINICAPTIMEOUT)
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
            try:

                # support py 3
                if not PY3:
                    frame = self.frame_gen.next()
                else:
                    frame = self.frame_gen.__next__()

                return frame
            except Exception as err:
                raise MinicapError(err)

    def update_rotation(self, rotation):
        """update rotation, and reset backend stream generator"""
        with self.stream_lock:
            self.size["rotation"] = rotation
            self.frame_gen = None
