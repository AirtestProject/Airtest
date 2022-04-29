# encoding=utf-8
import os
import time
import unittest
from airtest.core.ios.ios import IOS
from .testconf import is_port_open
DEFAULT_ADDR = "http://localhost:8100/"  # iOS设备连接参数
import warnings
warnings.simplefilter("always")


class TestInstructCmd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ios = IOS(DEFAULT_ADDR)
        cls.ihelper = cls.ios.instruct_helper

    @classmethod
    def tearDownClass(cls):
        pass

    def tearDown(self):
        self.ihelper.tear_down()

    def test_setup_proxy(self):
        port, _ = self.ihelper.setup_proxy(9100)
        self.assertTrue(is_port_open('localhost', port))

    def test_remove_proxy(self):
        port, _ = self.ihelper.setup_proxy(9100)
        self.assertTrue(is_port_open('localhost', port))
        time.sleep(2)
        self.ihelper.remove_proxy(port)
        time.sleep(2)
        self.assertFalse(is_port_open('localhost', port))

    def test_do_proxy_usbmux(self):
        # 仅当连接本地usb设备时才可用
        self.assertFalse(is_port_open('localhost', 9100))
        time.sleep(1)
        self.ihelper.do_proxy_usbmux(9100, 9100)
        time.sleep(5)
        self.assertTrue(is_port_open('localhost', 9100))

    def test_do_proxy(self):
        self.assertFalse(is_port_open('localhost', 9101))
        time.sleep(1)
        self.ihelper.do_proxy(9101, 9100)
        time.sleep(5)
        self.assertTrue(is_port_open('localhost', 9101))

    def test_do_proxy2(self):
        self.ihelper.do_proxy(9101, 9100)
        time.sleep(3)
        self.ihelper.remove_proxy(9101)

    def test_tear_down(self):
        port, _ = self.ihelper.setup_proxy(9100)
        self.assertTrue(is_port_open('localhost', port))
        self.ihelper.tear_down()
        time.sleep(3)
        self.assertFalse(is_port_open('localhost', port))
