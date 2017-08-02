# -*- coding: utf-8 -*-
from airtest.core.error import MoaError
from airtest.core.utils import SafeSocket, NonBlockingStreamReader, reg_cleanup, retries, get_logger
from airtest.core.android.adb import ADB
import struct
LOGGING = get_logger('javacap')


class Javacap(object):

    """another screencap class, slower than mincap, but better compatibility"""

    APP_PATH = "com.netease.nie.yosemite"
    SCREENCAP_SERVICE = "com.netease.nie.yosemite.Capture"
    DEVICE_PORT = "moa_javacap"
    CAPTIMEOUT = None

    def __init__(self, serialno, adb=None, localport=9999):
        self.serialno = serialno
        self.adb = adb or ADB(self.serialno)
        self.localport = localport
        self.frame_gen = None

    def get_path(self):
        output = self.adb.shell(['pm', 'path', self.APP_PATH])
        if 'package:' not in output:
            raise MoaError('package not found, output:[%s]' % output)
        return output.split(":")[1].strip()

    def _setup(self):
        # setup forward
        @retries(3)
        def set_up_forward():
            localport = self.localport or self.adb.get_available_forward_local()
            self.adb.forward("tcp:%s" % localport, "localabstract:%s" % self.DEVICE_PORT)
            return localport

        self.localport = set_up_forward()
        # setup agent proc
        apkpath = self.get_path()
        cmds = ["CLASSPATH=" + apkpath, 'exec', 'app_process', '/system/bin', self.SCREENCAP_SERVICE, "--scale", "100", "--socket", "%s" % self.DEVICE_PORT, "-lazy", "2>&1"]
        proc = self.adb.shell(cmds, not_wait=True)
        reg_cleanup(proc.kill)
        # check proc output
        nbsp = NonBlockingStreamReader(proc.stdout, print_output=True, name="javacap_sever")
        while True:
            line = nbsp.readline(timeout=5.0)
            if line is None:
                raise RuntimeError("javacap setup error")
            if "Capture server listening on" in line:
                break
            if "Address already in use" in line:
                raise RuntimeError("javacap setup error")

    def get_frames(self):
        self._setup()
        s = SafeSocket()
        s.connect(("localhost", self.localport))
        t = s.recv(24)
        # minicap info
        yield struct.unpack("<2B5I2B", t)

        while True:
            s.send(b"1")
            # recv header, count frame_size
            if self.CAPTIMEOUT is not None:
                header = s.recv_with_timeout(4, self.CAPTIMEOUT)
            else:
                header = s.recv(4)
            if header is None:
                LOGGING.error("javacap header is None")
                # recv timeout, if not frame updated, maybe screen locked
                yield None
            else:
                frame_size = struct.unpack("<I", header)[0]
                # recv image data
                one_frame = s.recv(frame_size)
                yield one_frame
        s.close()

    def get_frame(self):
        if self.frame_gen is None:
            self.frame_gen = self.get_frames()
            LOGGING.debug("javacap header: %s", str(self.frame_gen.next()))
        return self.frame_gen.next()
