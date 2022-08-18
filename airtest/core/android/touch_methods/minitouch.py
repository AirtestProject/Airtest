# -*- coding: utf-8 -*-
import os
import re
import socket
import sys
import warnings

from airtest.core.android.constant import STFLIB
from airtest.core.android.touch_methods.base_touch import BaseTouch
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.safesocket import SafeSocket
from airtest.utils.snippet import get_std_encoding, kill_proc, reg_cleanup

LOGGING = get_logger(__name__)


class Minitouch(BaseTouch):

    def __init__(self, adb, backend=False, size_info=None, input_event=None):
        super(Minitouch, self).__init__(adb, backend, size_info, input_event)
        self.default_pressure = 50
        self.path_in_android = "/data/local/tmp/minitouch"
        self.max_x, self.max_y = None, None
        self.localport = None

    def install(self):
        """
        Install minitouch

        Returns:
            None

        """

        abi = self.adb.getprop("ro.product.cpu.abi")
        sdk = int(self.adb.getprop("ro.build.version.sdk"))

        if sdk >= 16:
            binfile = "minitouch"
        else:
            binfile = "minitouch-nopie"

        device_dir = os.path.dirname(self.path_in_android)
        path = os.path.join(STFLIB, abi, binfile).replace("\\", r"\\")

        try:
            exists_file = self.adb.file_size(self.path_in_android)
        except:
            pass
        else:
            local_minitouch_size = int(os.path.getsize(path))
            if exists_file and exists_file == local_minitouch_size:
                LOGGING.debug("install_minitouch skipped")
                return
            self.uninstall()

        self.adb.push(path, "%s/minitouch" % device_dir)
        self.adb.shell("chmod 755 %s/minitouch" % (device_dir))
        LOGGING.info("install_minitouch finished")

    def uninstall(self):
        """
        Uninstall minitouch

        Returns:
            None

        """
        self.adb.raw_shell("rm " + self.path_in_android)

    def setup_server(self):
        """
        Setup minitouch server and adb forward

        Returns:
            server process

        """
        if self.server_proc:
            self.server_proc.kill()
            self.server_proc = None

        self.localport, deviceport = self.adb.setup_forward("localabstract:minitouch_{}".format)
        deviceport = deviceport[len("localabstract:"):]
        if self.input_event:
            p = self.adb.start_shell("/data/local/tmp/minitouch -n '{0}' -d '{1}' 2>&1".format(deviceport,self.input_event))
        else:
            p = self.adb.start_shell("/data/local/tmp/minitouch -n '{0}' 2>&1".format(deviceport))
        nbsp = NonBlockingStreamReader(p.stdout, name="minitouch_server", auto_kill=True)
        while True:
            line = nbsp.readline(timeout=3.0)
            if line is None:
                kill_proc(p)
                raise RuntimeError("minitouch setup timeout")

            line = line.decode(get_std_encoding(sys.stdout))

            # 识别出setup成功的log，并匹配出max_x, max_y
            m = re.search("Type \w touch device .+ \((\d+)x(\d+) with \d+ contacts\) detected on .+ \(.+\)", line)
            if m:
                self.max_x, self.max_y = int(m.group(1)), int(m.group(2))
                break
            else:
                self.max_x = 32768
                self.max_y = 32768
        if p.poll() is not None:
            # server setup error, may be already setup by others
            # subprocess exit immediately
            kill_proc(p)
            raise RuntimeError("minitouch server quit immediately")
        self.server_proc = p
        reg_cleanup(kill_proc, self.server_proc)
        return p

    def setup_client(self):
        """
        Setup client in following steps::

            1. connect to server
            2. receive the header
                v <version>
                ^ <max-contacts> <max-x> <max-y> <max-pressure>
                $ <pid>
            3. prepare to send

        Returns:
            None

        """
        s = SafeSocket()
        s.connect((self.adb.host, self.localport))
        s.sock.settimeout(2)
        header = b""
        while True:
            try:
                header += s.sock.recv(4096)  # size is not strict, so use raw socket.recv
            except socket.timeout:
                # raise RuntimeError("minitouch setup client error")
                warnings.warn("minitouch header not recved")
                break
            if header.count(b'\n') >= 3:
                break
        LOGGING.debug("minitouch header:%s", repr(header))
        self.client = s
        self.handle = self.safe_send

    def transform_xy(self, x, y):
        """
        Transform coordinates (x, y) according to the device display

        Args:
            x: coordinate x
            y: coordinate y

        Returns:
            transformed coordinates (x, y)

        """
        width, height = self.size_info['width'], self.size_info['height']
        nx = float(x) * self.max_x / width
        ny = float(y) * self.max_y / height
        return "%.0f" % nx, "%.0f" % ny

    def teardown(self):
        super(Minitouch, self).teardown()
        if self.localport:
            self.adb.remove_forward("tcp:{}".format(self.localport))
            self.localport = None
