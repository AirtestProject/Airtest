#!/usr/bin/env
# -*- coding: utf-8 -*-
import os
import unittest
from airtest.core.android.android import ADB
from airtest.core.helper import G
from airtest.core.settings import Settings as ST
from airtest.core.helper import set_logdir
from airtest.__main__ import main as main_parser
from airtest.report.report import LogToHtml, simple_report, DEFAULT_LOG_DIR, DEFAULT_LOG_FILE, HTML_FILE
from testconf import DIR, OWL, try_remove


class TestReport(unittest.TestCase):

    LOG_DIR = DIR(DEFAULT_LOG_DIR)
    OUTPUT_HTML = HTML_FILE
    EXPORT_DIR = DIR("export")
    HTTP_STATIC = "http://init.nie.netease.com/moa/new_report"
    SCRIPT_NAME = os.path.basename(OWL).replace(".air", "")

    @classmethod
    def setUpClass(cls):
        if not ADB().devices(state="device"):
            raise RuntimeError("At lease one adb device required")
        cls.delete_path([cls.OUTPUT_HTML, cls.EXPORT_DIR, cls.LOG_DIR])

    @classmethod
    def tearDownClass(cls):
        cls.delete_path([cls.OUTPUT_HTML, cls.EXPORT_DIR, cls.LOG_DIR])

    def setUp(self):
        self.delete_path([self.OUTPUT_HTML, self.EXPORT_DIR])
        if not os.path.exists(self.LOG_DIR):
            argv = ["run", OWL, "--device", "Android:///", "--log", self.LOG_DIR, "--recording"]
            main_parser(argv)

    def tearDown(self):
        self.delete_path([self.OUTPUT_HTML, self.EXPORT_DIR])

    @classmethod
    def delete_path(cls, path_list):
        for path in path_list:
            try_remove(path)

    def test_logtohtml_default(self):
        # All parameters use default parameters
        rpt = LogToHtml(OWL)
        rpt.report()
        self.assertTrue(os.path.exists(self.OUTPUT_HTML))

    def test_logtohtml_set_log(self):
        # set log_root
        rpt_logroot = LogToHtml(OWL, log_root=self.LOG_DIR)
        rpt_logroot.report()
        self.assertTrue(os.path.exists(self.OUTPUT_HTML))

    def test_logtohtml_script_py(self):
        # script_root is .py
        script_py = os.path.join(OWL, self.SCRIPT_NAME + ".py")
        rpt_py = LogToHtml(script_py)
        rpt_py.report()
        self.assertTrue(os.path.exists(self.OUTPUT_HTML))

    def test_set_logdir(self):
        new_logfile = "log123.txt"
        new_logdir = DIR("./logs_new")
        self.delete_path([new_logdir, new_logfile])
        # set logfile = ./logs_new/log123.txt
        ST.LOG_FILE = new_logfile
        set_logdir(new_logdir)
        argv = ["run", OWL, "--device", "Android:///"]
        main_parser(argv)
        G.LOGGER.set_logfile(None)
        self.assertTrue(os.path.exists(os.path.join(ST.LOG_DIR, ST.LOG_FILE)))

        rpt = LogToHtml(OWL)
        rpt.report()
        self.assertTrue(os.path.exists(self.OUTPUT_HTML))

        # test export log
        self.delete_path([self.EXPORT_DIR])
        rpt_export = LogToHtml(OWL, export_dir=self.EXPORT_DIR)
        rpt_export.report()
        export_path = os.path.join(self.EXPORT_DIR, self.SCRIPT_NAME + ".log")
        self.assertTrue(os.path.exists(os.path.join(export_path, self.OUTPUT_HTML)))
        self.assertTrue(os.path.exists(os.path.join(export_path, "static")))

        self.delete_path([new_logdir, new_logfile])
        ST.LOG_FILE = DEFAULT_LOG_FILE
        ST.LOG_DIR = DEFAULT_LOG_DIR

    def test_cli(self):
        argv = ["report", OWL, "--log_root", self.LOG_DIR, "--outfile", self.OUTPUT_HTML]
        main_parser(argv)
        self.assertTrue(os.path.exists(self.OUTPUT_HTML))

    def test_static_root_cli(self):
        argv = ["report", OWL, "--log_root", self.LOG_DIR, "--outfile", self.OUTPUT_HTML,
                "--static_root", self.HTTP_STATIC]
        main_parser(argv)
        self.assertTrue(os.path.exists(self.OUTPUT_HTML))
        with open(self.OUTPUT_HTML, encoding="utf-8", errors="ignore") as f:
            self.assertTrue(self.HTTP_STATIC in f.read())

    def test_static_root(self):
        # set static_root
        rpt = LogToHtml(OWL, self.LOG_DIR, static_root=self.HTTP_STATIC)
        rpt.report()
        self.assertTrue(os.path.exists(self.OUTPUT_HTML))
        with open(self.OUTPUT_HTML, encoding="utf-8", errors="ignore") as f:
            self.assertTrue(self.HTTP_STATIC in f.read())

    def test_output_file(self):
        rpt = LogToHtml(OWL)
        new_output_file = os.path.join(self.LOG_DIR, "new_log.html")
        rpt.report(output_file=new_output_file)
        self.assertTrue(os.path.exists(new_output_file))
        self.delete_path([new_output_file])

    def test_export_log(self):
        rpt = LogToHtml(OWL, export_dir=self.EXPORT_DIR)
        rpt.report()
        export_path = os.path.join(self.EXPORT_DIR, self.SCRIPT_NAME + ".log")
        self.assertTrue(os.path.exists(os.path.join(export_path, self.OUTPUT_HTML)))
        self.assertTrue(os.path.exists(os.path.join(export_path, "static")))

    def test_export_log_http_static(self):
        # http static file
        rpt_static = LogToHtml(OWL, export_dir=self.EXPORT_DIR, static_root=self.HTTP_STATIC)
        rpt_static.report()
        export_path = os.path.join(self.EXPORT_DIR, self.SCRIPT_NAME + ".log")
        self.assertTrue(os.path.exists(os.path.join(export_path, self.OUTPUT_HTML)))
        self.assertTrue(not os.path.exists(os.path.join(export_path, "static")))

    def test_simple_report(self):
        simple_report(OWL)
        self.assertTrue(os.path.exists(self.OUTPUT_HTML))


if __name__ == '__main__':
    unittest.main()
