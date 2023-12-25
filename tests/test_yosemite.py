# encoding=utf-8
from airtest.core.android.android import ADB, Javacap, YosemiteIme, YosemiteExt
from airtest.aircv.utils import string_2_img
from numpy import ndarray
import unittest
import warnings
warnings.simplefilter("always")


class TestJavacap(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()
        devices = cls.adb.devices()
        if not devices:
            raise RuntimeError("At lease one adb device required")
        cls.adb.serialno = devices[0][0]
        cls.javacap = Javacap(cls.adb)

    def test_0_get_frame(self):
        frame = self.javacap.get_frame_from_stream()
        frame = string_2_img(frame)
        self.assertIsInstance(frame, ndarray)

    def test_snapshot(self):
        img = self.javacap.snapshot()
        self.assertIsInstance(img, ndarray)

    def test_teardown(self):
        self.javacap.get_frame_from_stream()
        self.javacap.teardown_stream()

    @classmethod
    def tearDownClass(cls):
        cls.javacap.teardown_stream()


class TestIme(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()
        devices = cls.adb.devices()
        if not devices:
            raise RuntimeError("At lease one adb device required")
        cls.adb.serialno = devices[0][0]
        cls.ime = YosemiteIme(cls.adb)
        cls.ime.start()

    def test_text(self):
        self.ime.text("nimei")
        self.ime.text("你妹")

    def test_escape_text(self):
        self.ime.text("$call org/org->create_org($id,'test123')")
        self.ime.text("#@$%^&&*)_+!")

    def test_code(self):
        self.ime.text("test code")
        self.ime.code("2")

    def test_0_install(self):
        self.ime.yosemite.install_or_upgrade()
        self.ime.text("安装")

    def test_end(cls):
        cls.ime.end()


class TestYosemiteExt(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()
        devices = cls.adb.devices()
        if not devices:
            raise RuntimeError("At lease one adb device required")
        cls.adb.serialno = devices[0][0]
        cls.yosemite = YosemiteExt(cls.adb)

    def test_change_lang(self):
        self.yosemite.change_lang("ja")
        self.yosemite.change_lang("zh")

    def test_clipboard(self):
        text1 = "test clipboard"
        self.yosemite.set_clipboard(text1)
        self.assertEqual(self.yosemite.get_clipboard(), text1)

        # test escape special char
        text2 = "test clipboard with $pecial char #@!#%$#^&*()'"
        self.yosemite.set_clipboard(text2)
        self.assertEqual(self.yosemite.get_clipboard(), text2)



if __name__ == '__main__':
    unittest.main()
