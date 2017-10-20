# -*- coding: utf-8 -*-
import os
import sys
import unittest
import subprocess
from airtest.core.utils import get_adb_path




ADB_PATH = get_adb_path()
THIS_DIR = os.path.dirname(__file__)
TEST_PKG = "org.cocos.Rabbit"
TEST_APK = os.path.join(os.path.dirname(__file__), 'Rabbit.apk')
TEST_OWL = os.path.join(os.path.dirname(__file__), 'test_owl.owl')
KWARGS = "PKG=%s,APK=%s,SCRIPTHOME=%s" % (TEST_PKG, TEST_APK, THIS_DIR)
OUTPUT_HTML = 'log.html'
OUTPUT_GIF = 'log.gif'


class TestReportOnAndroid(unittest.TestCase):



    # TODO: can not run in subprocess mode,minitouch will stall
    @classmethod
    def setUpClass(cls):

        '''
        screen_dir = os.path.join(TEST_OWL, "img_record")
        if os.path.isdir(screen_dir):
            shutil.rmtree(screen_dir)
        log_file = os.path.join(TEST_OWL, "log.txt")
        if os.path.exists(log_file):
            with open(log_file, "w") as f:
                f.seek(0)
                f.truncate()
        cmd = "-m airtest run %s --setsn --kwargs %s --log" % (TEST_OWL, KWARGS)
        if six.PY2:
            cmd = "py -2 "+cmd
        else:
            cmd = "py -3 "+cmd

        proc = subprocess.Popen(cmd, shell=True)
        proc.wait()
        self.assertIs(proc.returncode, 0)'''

        # Test it in program
        pass
'''
    def setUp(self):
        if os.path.exists(OUTPUT_HTML):
            os.remove(OUTPUT_HTML)
        if os.path.exists(OUTPUT_GIF):
            os.remove(OUTPUT_GIF)

    def test_cli(self):
        cmd = "-m airtest report %s" % (TEST_OWL,)
        if six.PY2:
            cmd = "py -2 "+cmd
        else:
            cmd = "py -3 "+cmd
        proc = subprocess.Popen(cmd, shell=True)
        proc.wait()
        self.assertIs(proc.returncode, 0)
        self.assertTrue(os.path.exists(OUTPUT_HTML))

    def test_default_params(self):
        sys.argv = [sys.argv[0], TEST_OWL]

        ap = argparse.ArgumentParser()
        args=report.get_parger(ap).parse_args()

        report.main(args)
        self.assertTrue(os.path.exists(OUTPUT_HTML))

    def test_report_with_log_dir(self):
        sys.argv = [sys.argv[0], TEST_OWL, '--log', TEST_OWL]
        ap = argparse.ArgumentParser()
        args=report.get_parger(ap).parse_args()

        report.main(args)
        self.assertTrue(os.path.exists(OUTPUT_HTML))

    def test_gen_gif(self):
        sys.argv = [sys.argv[0], TEST_OWL, '--gif']
        ap = argparse.ArgumentParser()
        args=report.get_parger(ap).parse_args()

        report.main(args)
        self.assertTrue(os.path.exists(OUTPUT_GIF))'''


if __name__ == '__main__':
    unittest.main()
