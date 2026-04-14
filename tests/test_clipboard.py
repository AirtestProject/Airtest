# encoding=utf-8
import unittest
from airtest.core.android.android import ADB
from airtest.core.android.clipboard import ClipperClipboard, YosemiteClipboard

class TestClipboard(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()
        devices = cls.adb.devices()
        if not devices:
            raise RuntimeError("At lease one adb device required")
        cls.adb.serialno = devices[0][0]
        cls.yosemite_clipboard = YosemiteClipboard(cls.adb)
        cls.clipper_clipboard = ClipperClipboard(cls.adb)

    def test_clipboard(self):
        text1 = "test clipboard"
        text2 = "test clipboard with $pecial char #@!#%$#^&*()'"

        # test clipper clipboard
        self.clipper_clipboard.set_clipboard(text1)
        value = self.clipper_clipboard.get_clipboard()
        self.assertEqual(value, text1)

        self.clipper_clipboard.set_clipboard(text2)
        value = self.clipper_clipboard.get_clipboard()
        self.assertEqual(value, text2)

        
        # test yosemite clipboard
        self.yosemite_clipboard.set_clipboard(text1)
        value = self.yosemite_clipboard.get_clipboard()
        self.assertEqual(value, text1)

        self.yosemite_clipboard.set_clipboard(text2)
        value = self.yosemite_clipboard.get_clipboard()
        self.assertEqual(value, text2)