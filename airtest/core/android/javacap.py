# -*- coding: utf-8 -*-
from airtest.core.error import AirtestError
from airtest.utils.logger import get_logger
from airtest.utils.safesocket import SafeSocket
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.snippet import reg_cleanup
from airtest.core.android.adb import ADB
import struct
LOGGING = get_logger('javacap')


class Javacap(object):

    """another screencap class, slower than minicap, but better compatibility
       bug to be fixed: get_frame will return cached old screen, not always current screen
    """

    APP_PATH = "com.netease.nie.yosemite"
    SCREENCAP_SERVICE = "com.netease.nie.yosemite.Capture"
    CAPTIMEOUT = None

    def __init__(self, serialno, adb=None, localport=19998):
        self.serialno = serialno
        self.adb = adb or ADB(self.serialno)
        self.localport = localport
        self.frame_gen = None

    def get_path(self):
        output = self.adb.shell(['pm', 'path', self.APP_PATH])
        if 'package:' not in output:
            raise AirtestError('package not found, output:[%s]' % output)
        return output.split(":")[1].strip()

    def _setup(self):
        # setup forward
        self.localport, deviceport = self.adb.setup_forward("localabstract:javacap_{}".format)
        deviceport = deviceport[len("localabstract:"):]
        # setup agent proc
        apkpath = self.get_path()
        cmds = ["CLASSPATH=" + apkpath, 'exec', 'app_process', '/system/bin', self.SCREENCAP_SERVICE, "--scale", "100", "--socket", "%s" % deviceport, "-lazy", "2>&1"]
        proc = self.adb.start_shell(cmds)
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
        s.connect((self.adb.host, self.localport))
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
