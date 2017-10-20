#!/usr/bin/env
# -*- coding: utf-8 -*-
import os
import unittest
from airtest.core.android.android import ADB
from airtest.cli.__main__ import main as main_parser


THISDIR = os.path.dirname(__file__)
DIR = lambda x: os.path.join(THISDIR, x)
OWL = DIR("../playground/test_blackjack.owl")
OUTPUT_LOG = DIR("./log.txt")
OUTPUT_SCREEN = DIR("./img_record")
OUTPUT_HTML = DIR("./log.html")
OUTPUT_GIF = DIR("./log.gif")


class TestCli(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not ADB().devices(state="device"):
            raise RuntimeError("At lease one adb device required")

    def setUp(self):
        pass

    def test_info(self):
        argv = ["info", OWL]
        main_parser(argv)

    def test_run_android(self):
        argv = ["run", OWL, "--device", "Android:///", "--log"]
        main_parser(argv)
        self.assertTrue(os.path.exists(OUTPUT_LOG))

    def test_report(self):
        argv = ["report", OWL]
        main_parser(argv)
        self.assertTrue(os.path.exists(OUTPUT_HTML))

    def test_report_gif(self):
        argv = ["report", OWL, "--gif"]
        main_parser(argv)
        self.assertTrue(os.path.exists(OUTPUT_GIF))

    # todo: add tests run for difference args

    # def test_report_with_log_dir(self):
    #     sys.argv = [sys.argv[0], TEST_OWL, '--log', TEST_OWL]
    #     ap = argparse.ArgumentParser()
    #     args=report.get_parger(ap).parse_args()
    #
    #     report.main(args)
    #     self.assertTrue(os.path.exists(OUTPUT_HTML))

if __name__ == '__main__':
    unittest.main()
