import os
import sys
import unittest
import subprocess
from airtest.core.android.android import Android, ADB
from airtest import cli


TEST_PKG = "org.cocos.Rabbit"
TEST_APK = os.path.join(os.path.dirname(__file__), 'Rabbit.apk')
TEST_OWL = os.path.join(os.path.dirname(__file__), 'test_owl.owl')
KWARGS = "PKG=%s,APK=%s" % (TEST_PKG, TEST_APK)

class TestReportOnAndroid(unittest.TestCase):

    def test_android(self):
        cmd = "python -m airtest.cli %s --setsn --kwargs %s" % (TEST_OWL, KWARGS)
        proc = subprocess.Popen(cmd, shell=True)
        proc.wait()
        self.assertIs(proc.returncode, 0)

    def test_android_for_cover(self):
        sys.argv = [sys.argv[0], TEST_OWL, '--setsn', '--kwargs', KWARGS, '--log']
        try:
            cli.main()
        except SystemExit as err:
            self.assertEqual(err.message, 0)


if __name__ == '__main__':
    unittest.main()
