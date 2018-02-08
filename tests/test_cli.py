#!/usr/bin/env
# -*- coding: utf-8 -*-
import os
import unittest
from airtest.core.android.android import ADB
from airtest.core.helper import G
from airtest.__main__ import main as main_parser
from testconf import DIR, OWL, try_remove

OUTPUT_HTML = "./log.html"


class TestCli(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not ADB().devices(state="device"):
            raise RuntimeError("At lease one adb device required")

    @classmethod
    def tearDownClass(cls):
        G.LOGGER.set_logfile(None)
        try_remove(OUTPUT_HTML)

    def test_info(self):
        argv = ["info", OWL]
        main_parser(argv)

    def test_run_android(self):
        argv = ["run", OWL, "--device", "Android:///", "--log"]
        main_parser(argv)

        # test_report(self):
        try_remove(OUTPUT_HTML)
        argv = ["report", OWL]
        main_parser(argv)
        self.assertTrue(os.path.exists(OUTPUT_HTML))

    def test_report_with_log_dir(self):
        try_remove(OUTPUT_HTML)
        argv = ["run", OWL, "--device", "Android:///", "--log", DIR("./logs")]
        main_parser(argv)
        argv = ["report", OWL, "--log_root", DIR(".")]
        main_parser(argv)
        self.assertTrue(os.path.exists(OUTPUT_HTML))


if __name__ == '__main__':
    unittest.main()
