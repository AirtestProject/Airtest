import os
import sys
import unittest
import subprocess
from airtest.core.android.android import Android, ADB
from airtest import cli


TEST_PKG = "org.cocos.Rabbit"
TEST_APK = os.path.join(os.path.dirname(__file__), 'Rabbit.apk')
TEST_OWL = os.path.join(os.path.dirname(__file__), 'test_owl.owl')


class TestAirtestOnAndroid(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.serialno = ADB().devices(state="device")[0][0]
        self.android = Android(self.serialno)
        self.android.install_app(TEST_APK)

    def test_android(self):
        cmd = "python -m airtest.cli %s --setsn" % TEST_OWL
        proc = subprocess.Popen(cmd, shell=True)
        proc.wait()
        self.assertIs(proc.returncode, 0)


if __name__ == '__main__':
    unittest.main()
