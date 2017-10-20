from airtest.core.android.android import apkparser
import os
import unittest

TEST_APK = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Rabbit.apk')
TEST_PKG = "org.cocos.Rabbit"
TEST_VERSION = 1


class TestAPK(unittest.TestCase):

    def test_version(self):
        v = apkparser.version(TEST_APK)
        self.assertEqual(v, TEST_VERSION)

    def test_package(self):
        p = apkparser.packagename(TEST_APK)
        self.assertEqual(p, TEST_PKG)


if __name__ == '__main__':
    unittest.main()
