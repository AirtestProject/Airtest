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
        cls.yosemite_Clipboard = YosemiteClipboard(cls.adb)
        cls.clipper_clipboard = ClipperClipboard(cls.adb)

    def test_clipboard(self):
        # test clipper clipboard
        self.clipper_clipboard.set_clipboard("test clipper_clipboard")
        value = self.clipper_clipboard.get_clipboard()
        self.assertEqual(value, "test clipper_clipboard")
        
        # test yosemite clipboard
        self.yosemite_Clipboard.set_clipboard("test yosemite_clipboard")
        value = self.yosemite_Clipboard.get_clipboard()
        self.assertEqual(value, "test yosemite_clipboard")