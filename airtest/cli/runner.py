# -*- coding: utf-8 -*-

import unittest
import os
import shutil

from airtest.core.main import *  # noqa
from airtest.core.error import *  # noqa
from airtest.core.settings import Settings as ST


class AirtestCase(unittest.TestCase):

    SCRIPTEXT = ".owl"
    TPLEXT = ".png"

    @classmethod
    def setUpClass(cls):
        # init devices
        if isinstance(args.device, list):
            for device in args.device:
                init_device(device)
        elif args.device:
            init_device(args.device)

        # set logfile and screendir
        if args.log is True:
            print("save log & screen in script dir")
            ST.set_logdir(args.script)
        elif args.log:
            print("save log & screen in '%s'" % args.log)
            ST.set_logdir(args.log)
        else:
            print("do not save log & screen")
        set_logfile()
        set_screendir()
        ST.set_basedir(args.script)

        cls.scope = globals()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def runTest(self):
        scriptpath = args.script
        pyfilename = os.path.basename(scriptpath).replace(self.SCRIPTEXT, ".py")
        pyfilepath = os.path.join(scriptpath, pyfilename)
        pyfiledata = open(pyfilepath).read()
        exec(compile(pyfiledata, pyfilepath, 'exec')) in self.scope


def set_logfile():
    if ST.LOG_DIR:
        filepath = os.path.join(ST.LOG_DIR, ST.LOG_FILE)
        G.LOGGING.info("set_logfile %s", repr(os.path.realpath(filepath)))
        G.LOGGER.set_logfile(filepath)


def set_screendir():
    dirpath = os.path.join(ST.LOG_DIR, ST.SCREEN_DIR)
    shutil.rmtree(dirpath, ignore_errors=True)
    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)


def run_script(parsed_args, testcaseClass=AirtestCase):
    global args  # make it global to be used in AirtestCase & test scripts
    args = parsed_args
    suite = unittest.TestSuite()
    suite.addTest(testcaseClass())
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    from airtest.cli.parser import argparse, runner_parser
    ap = argparse.ArgumentParser()
    ap = runner_parser(ap)
    args = ap.parse_args()
    run_script(args)
