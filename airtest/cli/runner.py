# -*- coding: utf-8 -*-

import unittest
import os
import sys
import re
import shutil
import traceback
from airtest.core.api import *  # noqa
from airtest.core.error import *  # noqa
from airtest.core.settings import Settings as ST  # noqa
from airtest.core.helper import log
from airtest.utils.compat import decode_path
from copy import copy


class AirtestCase(unittest.TestCase):

    PROJECT_ROOT = "."
    SCRIPTEXT = ".air"
    TPLEXT = ".png"

    @classmethod
    def setUpClass(cls):
        cls.args = args
        # init devices
        if isinstance(args.device, list):
            devices = args.device
        elif args.device:
            devices = [args.device]
        else:
            devices = []
            print("do not connect device")

        for dev in devices:
            connect_device(dev)

        # set base dir to find tpl
        args.script = decode_path(args.script)
        G.BASEDIR = args.script

        # set log dir
        if args.log is True:
            print("save log in %s/log" % args.script)
            args.log = os.path.join(args.script, "log")
            set_logdir(args.log)
        elif args.log:
            print("save log in '%s'" % args.log)
            set_logdir(decode_path(args.log))
        else:
            print("do not save log")

        # setup script exec scope
        cls.scope = copy(globals())
        cls.scope["exec_script"] = cls.exec_other_script

        # set PROJECT_ROOT for exec other script
        cls.PROJECT_ROOT = os.environ.get("PROJECT_ROOT", ".")

    def setUp(self):
        if self.args.log and self.args.recording:
            for dev in G.DEVICE_LIST:
                try:
                    dev.start_recording()
                except:
                    traceback.print_exc()

    def tearDown(self):
        if self.args.log and self.args.recording:
            for k, dev in enumerate(G.DEVICE_LIST):
                try:
                    output = os.path.join(self.args.log, "recording_%d.mp4" % k)
                    dev.stop_recording(output)
                except:
                    traceback.print_exc()

    def runTest(self):
        log("main_script", {"script": self.args.script})
        scriptpath = self.args.script
        pyfilename = os.path.basename(scriptpath).replace(self.SCRIPTEXT, ".py")
        pyfilepath = os.path.join(scriptpath, pyfilename)
        pyfilepath = os.path.abspath(pyfilepath)
        code = open(pyfilepath).read()
        exec(compile(code, pyfilepath.encode(sys.getfilesystemencoding()), 'exec')) in self.scope

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

        # find script in PROJECT_ROOT
        scriptpath = os.path.join(cls.PROJECT_ROOT, scriptpath)
        # copy submodule's images into sub_dir
        sub_dir = _sub_dir_name(scriptpath)
        sub_dirpath = os.path.join(cls.args.script, sub_dir)
        _copy_script(scriptpath, sub_dirpath)
        # read code
        pyfilename = os.path.basename(scriptpath).replace(cls.SCRIPTEXT, ".py")
        pyfilepath = os.path.join(scriptpath, pyfilename)
        pyfilepath = os.path.abspath(pyfilepath)
        code = open(pyfilepath).read()
        # replace tpl filepath with filepath in sub_dir
        code = re.sub("[\'\"](\w+.png)[\'\"]", "\"%s/\g<1>\"" % sub_dir, code)
        exec(compile(code, pyfilepath, 'exec')) in cls.scope


def run_script(parsed_args, testcase_cls=AirtestCase):
    global args  # make it global deliberately to be used in AirtestCase & test scripts
    args = parsed_args
    suite = unittest.TestSuite()
    suite.addTest(testcase_cls())
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        sys.exit(-1)
