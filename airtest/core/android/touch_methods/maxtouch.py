# -*- coding: utf-8 -*-
import os

from airtest.core.android.constant import MAXTOUCH_JAR
from airtest.core.android.touch_methods.base_touch import BaseTouch
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.safesocket import SafeSocket
from airtest.utils.snippet import kill_proc

LOGGING = get_logger(__name__)


class Maxtouch(BaseTouch):

    def __init__(self, adb, backend=False, size_info=None, input_event=None):
        super(Maxtouch, self).__init__(adb, backend, size_info, input_event)
        self.default_pressure = 0.5
        self.path_in_android = "/data/local/tmp/maxpresent.jar"
        self.localport = None

    def install(self):
        """
        Install maxtouch

        Returns:
            None

        """
        try:
            exists_file = self.adb.file_size(self.path_in_android)
        except:
            pass
        else:
            local_minitouch_size = int(os.path.getsize(MAXTOUCH_JAR))
            if exists_file and exists_file == local_minitouch_size:
                LOGGING.debug("install_maxtouch skipped")
                return
            self.uninstall()

        self.adb.push(MAXTOUCH_JAR, self.path_in_android)
        self.adb.shell("chmod 755 %s" % self.path_in_android)
        LOGGING.info("install maxpresent.jar finished")

    def uninstall(self):
        """
        Uninstall maxtouch

        Returns:
            None

        """
        self.adb.raw_shell("rm %s" % self.path_in_android)

    def setup_server(self):
        """
        Setup maxtouch server and adb forward

        Returns:
            server process

        """
        if self.server_proc:
            self.server_proc.kill()
            self.server_proc = None

        self.localport, deviceport = self.adb.setup_forward("localabstract:maxpresent_{}".format)
        deviceport = deviceport[len("localabstract:"):]
        p = self.adb.start_shell("app_process -Djava.class.path={0} /data/local/tmp com.netease.maxpresent.MaxPresent socket {1}".format(self.path_in_android, deviceport))

        nbsp = NonBlockingStreamReader(p.stdout, name="airtouch_server", auto_kill=True)
        line = nbsp.readline(timeout=5.0)
        if line is None:
            kill_proc(p)
            raise RuntimeError("airtouch setup timeout")

        if p.poll() is not None:
            # server setup error, may be already setup by others
            # subprocess exit immediately
            kill_proc(p)
            raise RuntimeError("airtouch server quit immediately")
        self.server_proc = p
        return p

    def setup_client(self):
        """
        Setup client

        Returns:
            None

        """
        s = SafeSocket()
        s.connect((self.adb.host, self.localport))
        s.sock.settimeout(2)
        self.client = s
        self.handle = self.safe_send

    def transform_xy(self, x, y):
        """
        Normalized coordinates (x, y)

        Args:
            x: coordinate x
            y: coordinate y

        Returns:
            transformed coordinates (x, y)

        """
        width, height = self.size_info['width'], self.size_info['height']
        return x / width, y / height

    def teardown(self):
        super(Maxtouch, self).teardown()
        if self.localport:
            self.adb.remove_forward("tcp:{}".format(self.localport))
            self.localport = None
