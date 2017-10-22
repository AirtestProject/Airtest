#!/usr/bin/env
# -*- coding: utf-8 -*-
import os
import unittest
from airtest.core.android.android import ADB
from airtest.core.helper import G
from airtest.__main__ import main as main_parser
from testconf import DIR, OWL, try_remove

OUTPUT_LOG = DIR("./log.txt")
OUTPUT_SCREEN = DIR("./img_record")
OUTPUT_HTML = "./log.html"
OUTPUT_GIF = "./log.gif"


class TestCli(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not ADB().devices(state="device"):
            raise RuntimeError("At lease one adb device required")

    @classmethod
    def tearDownClass(cls):
        G.LOGGER.set_logfile(None)
        try_remove(OUTPUT_HTML)
        try_remove(OUTPUT_GIF)

    def test_info(self):
        argv = ["info", OWL]
        main_parser(argv)

    def test_run_android(self):
        argv = ["run", OWL, "--device", "Android:///"]
        main_parser(argv)

    def test_report(self):
        try_remove(OUTPUT_HTML)
        argv = ["report", OWL]
        main_parser(argv)
        self.assertTrue(os.path.exists(OUTPUT_HTML))

    def test_report_gif(self):
        try_remove(OUTPUT_GIF)
        argv = ["report", OWL, "--gif"]
        main_parser(argv)
        self.assertTrue(os.path.exists(OUTPUT_GIF))

    def test_report_with_log_dir(self):
        try_remove(OUTPUT_HTML)
        try_remove(OUTPUT_GIF)
        argv = ["run", OWL, "--device", "Android:///", "--log", DIR(".")]
        main_parser(argv)
        argv = ["report", OWL, "--log_root", DIR(".")]
        main_parser(argv)
        self.assertTrue(os.path.exists(OUTPUT_HTML))
        argv = ["report", OWL, "--gif", "--log_root", DIR(".")]
        main_parser(argv)
        self.assertTrue(os.path.exists(OUTPUT_GIF))


if __name__ == '__main__':
    unittest.main()
