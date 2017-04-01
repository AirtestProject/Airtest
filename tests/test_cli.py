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


class TestReportOnAndroid(unittest.TestCase):

    def test_android(self):
        cmd = "py -2 -m airtest run %s --setsn --kwargs %s --log" % (TEST_OWL, KWARGS)
        proc = subprocess.Popen(cmd, shell=True)
        proc.wait()
        self.assertIs(proc.returncode, 0)

    # def test_android_for_cover(self):
    #     sys.argv = [sys.argv[0], "run", TEST_OWL, '--setsn', '--kwargs', KWARGS, '--log']
    #     parser.main()


if __name__ == '__main__':
    unittest.main()
