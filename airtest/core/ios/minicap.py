# coding=utf-8
import subprocess
import os
import re
import struct
import logging
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.safesocket import SafeSocket
from airtest.utils.compat import SUBPROCESS_FLAG

LOGGING = get_logger(__name__)


class MinicapIOS(object):

    """https://github.com/openstf/ios-minicap"""
    CAPTIMEOUT = None

    def __init__(self, udid=None, port=12345):
        super(MinicapIOS, self).__init__()
        self.udid = udid or list_devices()[0]
        print(repr(self.udid))
        self.port = port
        self.resolution = "320x568"
        self.executable = os.path.join(os.path.dirname(__file__), "ios_minicap")
        self.server_proc = None

    def setup(self):
        cmd = [self.executable, "--udid", self.udid, "--port", str(self.port), "--resolution", self.resolution]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE, creationflags=SUBPROCESS_FLAG)
        nbsp = NonBlockingStreamReader(proc.stdout, print_output=True, name="minicap_sever")
        while True:
            line = nbsp.readline(timeout=10.0)
            if line is None:
                raise RuntimeError("minicap setup error")
            if b"== Banner ==" in line:
                break
        if proc.poll() is not None:
            logging.warn("Minicap server already started, use old one")
        self.server_proc = proc

    def get_frames(self):
        """
        rotation is alwary right on iOS
        """
        s = SafeSocket()
        s.connect(("localhost", self.port))
        t = s.recv(24)
        # minicap info
        print(struct.unpack("<2B5I2B", t))

        while True:
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


def list_devices():
    cmd = "system_profiler SPUSBDataType"
    ret = subprocess.check_output(cmd, shell=True).strip() or None
    m = re.findall(r"(?:iPhone|iPad).*?Serial Number: (\w+)", ret, re.DOTALL)
    print(m)
    return m


if __name__ == '__main__':
    m = MinicapIOS()
    m.setup()
    gen = m.get_frames()
    for i in range(100):
        img = next(gen)
        with open("name_%s.png" % i, "wb") as f:
            f.write(img)
