# -*- coding: utf-8 -*-

import unittest
import os
import sys
import six
import re
import shutil
import traceback
import warnings
from io import open
from airtest.core.api import G, auto_setup, log
from airtest.core.settings import Settings as ST
from airtest.utils.compat import decode_path, script_dir_name, script_log_dir
from copy import copy


class AirtestCase(unittest.TestCase):

    PROJECT_ROOT = "."
    SCRIPTEXT = ".air"
    TPLEXT = ".png"

    @classmethod
    def setUpClass(cls):
        cls.args = args

        setup_by_args(args)

        # setup script exec scope
        cls.scope = copy(globals())
        cls.scope["exec_script"] = cls.exec_other_script

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
        scriptpath, pyfilename = script_dir_name(self.args.script)
        pyfilepath = os.path.join(scriptpath, pyfilename)
        pyfilepath = os.path.abspath(pyfilepath)
        self.scope["__file__"] = pyfilepath
        with open(pyfilepath, 'r', encoding="utf8") as f:
            code = f.read()
        pyfilepath = pyfilepath.encode(sys.getfilesystemencoding())

        try:
            exec(compile(code.encode("utf-8"), pyfilepath, 'exec'), self.scope)
        except Exception as err:
            tb = traceback.format_exc()
            log("Final Error", tb)
            six.reraise(*sys.exc_info())

    @classmethod
    def exec_other_script(cls, scriptpath):
        """run other script in test script"""

        warnings.simplefilter("always")
        warnings.warn("please use using() api instead.", PendingDeprecationWarning)

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
        scriptpath = os.path.join(ST.PROJECT_ROOT, scriptpath)
        # copy submodule's images into sub_dir
        sub_dir = _sub_dir_name(scriptpath)
        sub_dirpath = os.path.join(cls.args.script, sub_dir)
        _copy_script(scriptpath, sub_dirpath)
        # read code
        pyfilename = os.path.basename(scriptpath).replace(cls.SCRIPTEXT, ".py")
        pyfilepath = os.path.join(scriptpath, pyfilename)
        pyfilepath = os.path.abspath(pyfilepath)
        with open(pyfilepath, 'r', encoding='utf8') as f:
            code = f.read()
        # replace tpl filepath with filepath in sub_dir
        code = re.sub("[\'\"](\w+.png)[\'\"]", "\"%s/\g<1>\"" % sub_dir, code)
        exec(compile(code.encode("utf8"), pyfilepath, 'exec'), cls.scope)


def setup_by_args(args):
    # init devices
    if isinstance(args.device, list):
        devices = args.device
    elif args.device:
        devices = [args.device]
    else:
        devices = []
        print("do not connect device")

    # set base dir to find tpl
    dirpath, _ = script_dir_name(args.script)

    # set log dir
    if args.log:
        args.log = script_log_dir(dirpath, args.log)
        print("save log in '%s'" % args.log)
    else:
        print("do not save log")

    # guess project_root to be basedir of current .air path
    project_root = os.path.dirname(args.script) if not ST.PROJECT_ROOT else None

    auto_setup(dirpath, devices, args.log, project_root)


def run_script(parsed_args, testcase_cls=AirtestCase):
    global args  # make it global deliberately to be used in AirtestCase & test scripts
    args = parsed_args
    suite = unittest.TestSuite()
    suite.addTest(testcase_cls())
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        sys.exit(-1)
