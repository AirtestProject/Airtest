# encoding=utf-8
# from airtest.core.api import *
import os
from airtest.core.api import connect_device, start_app, stop_app, install
from airtest.core.assertions import *
from airtest.core.helper import G
from airtest.core.settings import Settings as ST
from airtest.core.cv import Template
from airtest.core.android.android import Android, CAP_METHOD
from airtest.core.error import TargetNotFoundError, AdbShellError
from airtest.report.report import DEFAULT_LOG_DIR
from .testconf import APK, PKG, TPL, TPL2, DIR, try_remove
import unittest
import warnings
warnings.simplefilter("always")


class TestAssertionsOnAndroid(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.LOG_DIR = DIR(DEFAULT_LOG_DIR)
        if not isinstance(G.DEVICE, Android):
            connect_device("Android:///")
        cls.dev = G.DEVICE
        ST.LOG_DIR = cls.LOG_DIR

    def setUp(self):
        try_remove(self.LOG_DIR)
        try:
            os.mkdir(self.LOG_DIR)
        except FileExistsError:
            pass

    def tearDown(self):
        try_remove(self.LOG_DIR)

    def _start_apk_main_scene(self):
        if PKG not in self.dev.list_app():
            install(APK)
        stop_app(PKG)
        start_app(PKG)

    def test_assert_exists(self):
        self._start_apk_main_scene()
        assert_exists(TPL)
        with self.assertRaises(AssertionError):
            assert_exists(TPL2)
        stop_app(PKG)

    def test_assert_not_exists(self):
        self._start_apk_main_scene()
        assert_not_exists(TPL2)

        with self.assertRaises(AssertionError):
            assert_not_exists(TPL)
        stop_app(PKG)

    def test_assert_equal(self):
        with self.assertRaises(AssertionError):
            assert_equal(1, 2)

        assert_equal(1+1, 2, snapshot=False)

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 1, "snapshot should be saved only once")

    def test_assert_not_equal(self):
        with self.assertRaises(AssertionError):
            assert_not_equal(1, 1, "assert not equal")

        assert_not_equal(1, 2)
        self.assertEqual(len(os.listdir(self.LOG_DIR)), 2)

    def test_assert_true(self):
        # bool(expr) is True
        assert_true(True)
        assert_true(1 == 1)
        assert_true("123")
        assert_true("FOO".isupper())
        with self.assertRaises(AssertionError):
            assert_true("", "msg")

        with self.assertRaises(AssertionError):
            assert_true(None)

        with self.assertRaises(AssertionError):
            assert_true(1 == 2, snapshot=False)

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 6)

    def test_assert_false(self):
        # bool(expr) is False
        assert_false(False)
        assert_false(1==2)
        assert_false(None)
        assert_false([])
        with self.assertRaises(AssertionError):
            assert_false(1==1)

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 5)

    def test_assert_is(self):
        assert_is(TPL, TPL)
        assert_is(1, 1)
        with self.assertRaises(AssertionError):
            assert_is(1, 2)

        with self.assertRaises(AssertionError):
            assert_is(1, "1")

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 4)

    def test_assert_is_not(self):
        assert_is_not(TPL, TPL2)
        assert_is_not(1, 2)
        assert_is_not(1, "1")
        with self.assertRaises(AssertionError):
            assert_is_not(1, 1)

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 4)

    def test_assert_is_none(self):
        assert_is_none(None)
        with self.assertRaises(AssertionError):
            assert_is_none(1)

        with self.assertRaises(AssertionError):
            assert_is_none([])

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 3)

    def test_assert_is_not_none(self):
        assert_is_not_none(1, snapshot=False)
        assert_is_not_none(self.dev)
        with self.assertRaises(AssertionError):
            assert_is_not_none(None)

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 2)

    def test_assert_in(self):
        assert_in(TPL, [TPL, TPL2])
        with self.assertRaises(AssertionError):
            assert_in(3, [1, 2])

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 2)

    def test_assert_not_in(self):
        assert_not_in(3, [1, 2])
        with self.assertRaises(AssertionError):
            assert_not_in(TPL, [TPL, TPL2])

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 2)

    def test_assert_is_instance(self):
        assert_is_instance(TPL, Template)
        with self.assertRaises(AssertionError):
            assert_is_instance(1, str)

        assert_is_instance(1, type(2))

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 3)

    def test_assert_not_is_instance(self):
        assert_not_is_instance(1, str)
        with self.assertRaises(AssertionError):
            assert_not_is_instance(TPL, Template)

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 2)

    def test_assert_greater(self):
        assert_greater(2, 1)
        with self.assertRaises(AssertionError):
            assert_greater(1, 1)

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 2)

    def test_assert_greater_equal(self):
        assert_greater_equal(2, 1)
        assert_greater_equal(1, 1)
        with self.assertRaises(AssertionError):
            assert_greater_equal(1, 2)

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 3)

    def test_assert_less(self):
        assert_less(1, 2)
        with self.assertRaises(AssertionError):
            assert_less(1, 1)

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 2)

    def test_assert_less_equal(self):
        assert_less_equal(1, 2)
        assert_less_equal(1, 1)
        with self.assertRaises(AssertionError):
            assert_less_equal(2, 1)

        self.assertEqual(len(os.listdir(self.LOG_DIR)), 3)


if __name__ == '__main__':
    unittest.main()
