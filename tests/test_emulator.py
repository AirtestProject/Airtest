import os
import sys
import unittest
import subprocess
from airtest.core.android.android import Android, ADB
from airtest.cli import parser

THIS_DIR = os.path.dirname(__file__)
TEST_PKG = "org.cocos.Rabbit"
TEST_APK = os.path.join(THIS_DIR, 'Rabbit.apk')
TEST_OWL = os.path.join(THIS_DIR, 'test_owl.owl')
KWARGS = "PKG=%s,APK=%s,SCRIPTHOME=%s" % (TEST_PKG, TEST_APK, THIS_DIR)


class TestAndroidOnEmulator(unittest.TestCase):

    def test_run(self):
        sys.argv = [sys.argv[0], "run", TEST_OWL, '--setsn', '192.168.56.101:5555', '--kwargs', KWARGS, '--log']
        parser.main()


if __name__ == '__main__':
    unittest.main()

