# encoding=utf-8
import os
import time
import unittest
from airtest.core.ios.ios import IOS, CAP_METHOD
from airtest import aircv
from .testconf import try_remove, is_port_open
import warnings
warnings.simplefilter("always")

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
        cls.mjpeg_server.teardown_stream()

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
        # mjpeg直接截图，可能图像不是最新的
        for i in range(3):
            screen = self.mjpeg_server.snapshot(ensure_orientation=True)
            aircv.show(screen)
            time.sleep(2)

    def test_frame_resume(self):
        """
        用于测试当连接建立一段时间后，暂停接受数据，然后恢复数据的效果
        Returns:

        """
        import cv2
        for i in range(20):
            data = self.mjpeg_server.get_frame_from_stream()
            img = aircv.utils.string_2_img(data)
            cv2.imshow("test", img)
            c = cv2.waitKey(10)
            time.sleep(0.05)
        time.sleep(10)
        for i in range(200):
            data = self.mjpeg_server.get_frame_from_stream()
            img = aircv.utils.string_2_img(data)
            cv2.imshow("test", img)
            c = cv2.waitKey(10)
            time.sleep(0.05)
        cv2.destroyAllWindows()

    def test_get_blank_screen(self):
        img_string = self.mjpeg_server.get_blank_screen()
        img = aircv.utils.string_2_img(img_string)
        aircv.show(img)

    def test_teardown_stream(self):
        self.mjpeg_server.get_frame()
        if self.mjpeg_server.port_forwarding is True:
            self.assertTrue(is_port_open(self.mjpeg_server.ip, self.mjpeg_server.port))
            self.mjpeg_server.teardown_stream()
            self.assertFalse(is_port_open(self.mjpeg_server.ip, self.mjpeg_server.port))
