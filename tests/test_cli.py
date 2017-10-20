#!/usr/bin/env
# -*- coding: utf-8 -*-
import os
import sys
import unittest
import subprocess
import threading
import argparse
import six
import shutil
from airtest.core.android.android import Android, ADB
from airtest.cli import parser
from airtest.cli.runner import *
from airtest.core.utils import get_adb_path
from airtest.report import report



ADB_PATH = get_adb_path()
THIS_DIR = os.path.dirname(__file__)
TEST_PKG = "org.cocos.Rabbit"
TEST_APK = os.path.join(THIS_DIR, 'Rabbit.apk')
TEST_OWL = os.path.join(THIS_DIR, 'test_owl.owl')
UTIL_FILE = os.path.join(THIS_DIR, 'util.txt')
KWARGS = "PKG=%s,APK=%s,SCRIPTHOME=%s" % (TEST_PKG, TEST_APK, THIS_DIR)
OUTPUT_HTML = 'log.html'
OUTPUT_GIF = 'log.gif'

class TestCLIAndReport(unittest.TestCase):

    # TODO: can not run in subprocess mode,minitouch will stall
    def _test_android(self):
        print(KWARGS)

        cmd = "-m airtest run %s --setsn --kwargs %s --log" % (TEST_OWL, KWARGS)
        if six.PY2:
            cmd = "py -2 "+cmd
        else:
            cmd = "py -3 "+cmd
        proc = subprocess.Popen(cmd, shell=True)
        proc.wait()
        self.assertIs(proc.returncode, 0)

    def test_aandroid_other(self):
        sys.argv = [sys.argv[0], 'run', TEST_OWL, '--setsn', '--kwargs', KWARGS, '--log']

        ap = parser.get_parser()
        args = ap.parse_args()
        run_script(args)

    def test_forever(self):
        print (KWARGS)
        cmd = "py -2 -m airtest run test --forever"
        #proc = subprocess.Popen(cmd, shell=True)
        #timer = threading.Timer(5, proc.kill)
        #timer.start()
        #ret = proc.wait()
        #self.assertIs(proc.returncode, 0)


    def setUp(self):
        if os.path.exists(OUTPUT_HTML):
            os.remove(OUTPUT_HTML)
        if os.path.exists(OUTPUT_GIF):
            os.remove(OUTPUT_GIF)

    def test_report_cli(self):
        cmd = "-m airtest report %s" % (TEST_OWL,)
        if six.PY2:
            cmd = "py -2 "+cmd
        else:
            cmd = "py -3 "+cmd
        proc = subprocess.Popen(cmd, shell=True)
        proc.wait()
        self.assertIs(proc.returncode, 0)
        self.assertTrue(os.path.exists(OUTPUT_HTML))

    def test_report_default_params(self):
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
        self.assertTrue(os.path.exists(OUTPUT_GIF))



    # def test_android_for_cover(self):
    #     sys.argv = [sys.argv[0], "run", TEST_OWL, '--setsn', '--kwargs', KWARGS, '--log']
    #     parser.main()


if __name__ == '__main__':
    unittest.main()
