from airtest.core.android.apkparser.apk import APK as apkparser
from testconf import APK, PKG
import unittest


class TestAPK(unittest.TestCase):

    def test_version(self):
        v = apkparser(APK).androidversion_code
        self.assertEqual(v, "1")

    def test_package(self):
        p = apkparser(APK).get_package()
        self.assertEqual(p, PKG)


if __name__ == '__main__':
    unittest.main()
