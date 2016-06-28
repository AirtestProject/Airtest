from moa.core.android.android import Android, ADB, adb_devices, Minicap, Minitouch
from moa import report
print report
import unittest


class TestAndroid(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.serialno = adb_devices(state="device").next()[0]
        self.android = Android(self.serialno)

    def test_serialno(self):
        self.assertEqual(self.android.serialno, self.serialno)

    def test_adb(self):
        self.assertIsInstance(self.android.adb, ADB)

    def test_size(self):
        self.assertIn("width", self.android.size)
        self.assertIn("height", self.android.size)
        self.assertIn("orientation", self.android.size)
        self.assertIn("rotation", self.android.size)

    def test_minicap(self):
        minicap = self.android.minicap
        self.assertIsInstance(minicap, Minicap)
        self.assertIs(minicap.size, self.android.size)

    def test_minitouch(self):
        self.assertIsInstance(self.android.minitouch, Minitouch)


if __name__ == '__main__':
    unittest.main()
