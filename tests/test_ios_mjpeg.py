# encoding=utf-8
import os
import time
import unittest
from airtest.core.ios.ios import IOS, CAP_METHOD
from airtest import aircv
from .testconf import try_remove, is_port_open

DEFAULT_ADDR = "http://localhost:8100/"  # iOS设备连接参数
DEFAULT_PORT = 9100


class TestIosMjpeg(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ios = IOS(DEFAULT_ADDR, cap_method=CAP_METHOD.MJPEG, mjpeg_port=DEFAULT_PORT)
        cls.mjpeg_server = cls.ios.mjpegcap

    @classmethod
    def tearDownClass(cls):
        try_remove('screen.png')

    def test_get_frame(self):
        for i in range(5):
            data = self.mjpeg_server.get_frame()
            filename = "./screen.jpg"
            with open(filename, "wb") as f:
                f.write(data)
            self.assertTrue(os.path.exists(filename))
            time.sleep(2)

    def test_snapshot(self):
        # 测试截图，可以手动将设备横屏后再运行确认截图的方向是否正确
        screen = self.mjpeg_server.snapshot(ensure_orientation=True)
        aircv.show(screen)

    def test_teardown_stream(self):
        self.mjpeg_server.get_frame()
        if self.mjpeg_server.port_forwarding is True:
            self.assertTrue(is_port_open(self.mjpeg_server.ip, self.mjpeg_server.port))
            self.mjpeg_server.teardown_stream()
            self.assertFalse(is_port_open(self.mjpeg_server.ip, self.mjpeg_server.port))
