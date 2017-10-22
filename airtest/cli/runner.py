# -*- coding: utf-8 -*-

import unittest
import os
import re
import shutil

from airtest.core.api import *  # noqa
from airtest.core.error import *  # noqa
from airtest.core.settings import Settings as ST
from airtest.core.helper import log
from copy import copy


class AirtestCase(unittest.TestCase):

    SCRIPTHOME = "."
    SCRIPTEXT = ".owl"
    TPLEXT = ".png"

    @classmethod
    def setUpClass(cls):
        # init devices
        if isinstance(args.device, list):
            devices = args.device
        elif args.device:
            devices = [args.device]
        else:
            # default to use local android device
            devices = ["Android:///"]
        for device in devices:
            connect_device(device)

        cls.script = args.script
        cls.pre = args.pre
        cls.post = args.post

        # set basedir to find tpl
        G.BASEDIR = cls.script

        # set logfile and screendir
        if args.log is True:
            print("save log & screen in script dir")
            ST.LOG_DIR = cls.script
        elif args.log:
            print("save log & screen in '%s'" % args.log)
            ST.LOG_DIR = args.log
        else:
            print("save log in cwd as default")
        # set log file
        logfile = os.path.join(ST.LOG_DIR, ST.LOG_FILE)
        print("set_logfile %s", repr(os.path.realpath(logfile)))
        G.LOGGER.set_logfile(logfile)
        # make screen dir
        dirpath = os.path.join(ST.LOG_DIR, ST.SCREEN_DIR)
        shutil.rmtree(dirpath, ignore_errors=True)
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath)

        # setup script exec scope
        cls.scope = copy(globals())
        cls.scope["exec_script"] = cls.exec_other_script

        # add user defined global varibles
        if args.kwargs:
            print("load kwargs", repr(args.kwargs))
            for kv in args.kwargs.split(","):
                k, v = kv.split("=")
                cls.scope[k] = v

    def setUp(self):
        if self.pre:
            log("pre_script", {"script": self.pre})
            self.exec_other_script(self.pre)

    def tearDown(self):
        if self.post:
            log("post_script", {"script": self.pre})
            self.exec_other_script(self.post)

    def runTest(self):
        scriptpath = self.script
        pyfilename = os.path.basename(scriptpath).replace(self.SCRIPTEXT, ".py")
        pyfilepath = os.path.join(scriptpath, pyfilename)
        code = open(pyfilepath).read()
        exec(compile(code, pyfilepath, 'exec')) in self.scope

    @classmethod
    def exec_other_script(cls, scriptpath):
        """run other script in test script"""

        def _sub_dir_name(scriptname):
            dirname = os.path.splitdrive(os.path.normpath(scriptname))[-1]
            dirname = dirname.strip(os.path.sep).replace(os.path.sep, "_").replace(cls.SCRIPTEXT, "_sub")
            return dirname

        def _copy_script(src, dst):
            if os.path.isdir(dst):
                shutil.rmtree(dst, ignore_errors=True)
            os.mkdir(dst)
            for f in os.listdir(src):
                srcfile = os.path.join(src, f)
                if not (os.path.isfile(srcfile) and f.endswith(cls.TPLEXT)):
                    continue
                dstfile = os.path.join(dst, f)
                shutil.copy(srcfile, dstfile)

        # find script in SCRIPTHOME
        scriptpath = os.path.join(cls.SCRIPTHOME, scriptpath)
        # copy submodule's images into sub_dir
        sub_dir = _sub_dir_name(scriptpath)
        sub_dirpath = os.path.join(cls.script, sub_dir)
        _copy_script(scriptpath, sub_dirpath)
        # read code
        pyfilename = os.path.basename(scriptpath).replace(cls.SCRIPTEXT, ".py")
        pyfilepath = os.path.join(scriptpath, pyfilename)
        code = open(pyfilepath).read()
        # replace tpl filepath with filepath in sub_dir
        code = re.sub("[\'\"](\w+.png)[\'\"]", "\"%s/\g<1>\"" % sub_dir, code)
        exec(compile(code, pyfilepath, 'exec')) in cls.scope


def run_script(parsed_args, testcase_cls=AirtestCase):
    global args  # make it global delibrately to be used in AirtestCase & test scripts
    args = parsed_args
    suite = unittest.TestSuite()
    suite.addTest(testcase_cls())
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        exit(-1)
