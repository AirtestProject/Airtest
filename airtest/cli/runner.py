#!/usr/bin/env
# -*- coding: utf-8 -*-

import re
import os
import sys
import shutil
import traceback
from urllib import unquote
from airtest.core.main import *
from airtest.core.error import MinicapError, MinitouchError, AdbError
from airtest.core.helper import log, logwrap
from airtest.core.settings import Settings as ST
try:
    from minitest.qa import UI, MO, QC, Base as minitest
except ImportError as e:
    minitest = None


SCRIPT_STACK = []
SCRIPTEXT = ".owl"
TPLEXT = ".png"


def run_script(args):
    # loading util file
    if args.utilfile:
        if os.path.isfile(args.utilfile):
            print "try loading:", args.utilfile
            sys.path.append(os.path.dirname(args.utilfile))
            utilcontent = open(args.utilfile).read()
            exec(compile(utilcontent, args.utilfile, 'exec')) in globals()
        else:
            print "file does not exist:", os.path.abspath(args.utilfile)

    if args.setsn is not None:
        print "set_serialno", args.setsn
        minicap = not args.nominicap
        minitouch = not args.nominitouch
        if args.setsn == "":
            for i in range(args.devcount):
                # auto choose one serialno
                set_serialno(minicap=minicap, minitouch=minitouch)
        else:
            for sn in args.setsn.split(","):
                set_serialno(sn, minicap=minicap, minitouch=minitouch)
        set_current(0)
        if minitest:
            minitest.set_global()

    if args.setudid is not None:  # modified by gzlongqiumeng
        print "set_udid", args.setudid
        udid = args.setudid if isinstance(args.setudid, str) else None
        set_udid(udid)

    if args.setwin is not None:
        print "set_windows", args.setwin
        if args.setwin == "":
            for i in range(args.devcount):
                # auto choose one window
                set_windows()
        else:
            for handle in args.setwin.split(","):
                set_windows(handle=int(handle))
        set_current(0)

    if args.setemulator:
        print "set_emulator", args.setemulator  # add by zq
        emu_name = args.setemulator if isinstance(args.setemulator, str) else None
        if args.setadb:
            addr = args.setadb.split(":")
            set_emulator(emu_name, addr=addr)
        else:
            set_emulator(emu_name)

    if args.kwargs:
        print "load kwargs", repr(args.kwargs)
        for kv in args.kwargs.split(","):
            k, v = kv.split("=")
            if k == "findoutside":  # if extra arg is findoutside, set airtest-FINDOUTSIDE
                # set_find_outside(v)
                ST.set_find_outside(v)
            else:
                globals()[k] = v

    # run script
    if args.log is True:
        print "save log & screen in script dir"
        ST.set_logdir(args.script)
    elif args.log:
        print "save log & screen in '%s'" % args.log
        ST.set_logdir(args.log)
    else:
        print "do not save log & screen"
    set_logfile()
    set_screendir()

    # run script in forever mode, read input & exec
    if args.forever:
        run_forever(args)

    on_device_ready()
    # set root script as basedir
    # SCRIPT_STACK.append(args.script)
    try:
        # execute pre script
        if args.pre:
            ST.set_basedir(args.pre)
            for i in range(len(G.DEVICE_LIST)):  # pre for all devices
                set_current(i)
                exec_script(args.pre, scope=globals(), root=True)

        # execute script
        ST.set_basedir(args.script)
        set_current(0)
        exec_script(args.script, scope=globals(), root=True)
    except:
        err = traceback.format_exc()
        # log("error", {"traceback": err}, False)
        raise
    finally:
        # execute post script, whether pre & script succeed or not
        if args.post:
            try:
                ST.set_basedir(args.post)
                for i in range(len(G.DEVICE_LIST)):  # post for all devices
                    set_current(i)
                    exec_script(args.post, scope=globals(), root=True)
            except:
                # log("error", {"traceback": traceback.format_exc()}, False)
                traceback.print_exc()


def exec_script(scriptname, scope=None, root=False, code=None):
    """
    execute script: root or submodule
    1. exec root script
    2. if submodule script:
        2.1 cp imgs to sub_dir
        2.2 exec sub script
    """
    global SCRIPT_STACK
    if root:
        scriptpath = scriptname
        SCRIPT_STACK = []
    elif os.path.isabs(scriptname):
        scriptpath = scriptname
    else:
        if not SCRIPTHOME:
            raise RuntimeError("SCRIPTHOME not set, please set_scripthome first")
        scripthome = os.path.abspath(SCRIPTHOME)
        scriptpath = os.path.join(scripthome, scriptname)
    SCRIPT_STACK.append(scriptname)

    # start exec
    print "exec_script", scriptpath
    # read code
    if code is None:
        pyfilename = os.path.basename(scriptname).replace(SCRIPTEXT, ".py")
        pyfilepath = os.path.join(scriptpath, pyfilename)
        # code = open(pyfilepath).read()
        try:
            with open(pyfilepath) as pyfile:
                code = pyfile.read()
        except Exception as err:
            traceback.print_exc()
            code = ""

    # handle submodule script
    if not root:
        # copy submodule's images into sub_dir
        sub_dir = _sub_dir_name(scriptname)
        sub_dirpath = os.path.join(SCRIPT_STACK[0], sub_dir)
        _copy_script(scriptpath, sub_dirpath)
        # replace tpl filepath with filepath in sub_dir
        code = re.sub("[\'\"](\w+.png)[\'\"]", "\"%s/\g<1>\"" % sub_dir, code)
    # exec code
    if scope:
        # exec(compile(code, scriptname, 'exec')) in scope
        exec(compile(code, scriptname, 'exec')) in scope
    else:
        exec(compile(code, scriptname, 'exec')) in globals()
    # finish exec
    SCRIPT_STACK.pop()
    return scriptpath


def _copy_script(src, dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst, ignore_errors=True)
    os.mkdir(dst)
    for f in os.listdir(src):
        srcfile = os.path.join(src, f)
        if not (os.path.isfile(srcfile) and f.endswith(TPLEXT)):
            continue
        dstfile = os.path.join(dst, f)
        shutil.copy(srcfile, dstfile)


def _sub_dir_name(scriptname):
    dirname = os.path.splitdrive(os.path.normpath(scriptname))[-1]
    dirname = dirname.strip(os.path.sep).replace(os.path.sep, "_").replace(SCRIPTEXT, "_sub")
    return dirname


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


def set_threshold(value):
    ST.set_threshold(value)


def set_scripthome(dirpath):
    global SCRIPTHOME
    SCRIPTHOME = dirpath


def get_globals(key):
    return getattr(ST, key)


def set_globals(key, value):
    if callable(value):
        value = staticmethod(value)
    setattr(ST, key, value)


def device():
    # return get_globals("DEVICE")
    return G.DEVICE


def on_device_ready():
    """to be overwritten by users"""
    pass


def _exec_script_for_forever(args, script, code=None):

    # --------------------------------------------------------------报错..
    charset = sys.stdin.encoding or 'utf8'
    script = script.decode(charset)

    # script = script.decode(sys.stdin.encoding)
    ST.set_basedir(script)

    try:
        exec_script(script, scope=globals(), root=True, code=code)
    except (MinitouchError, MinicapError, AdbError) as e:
        raise e
    except:
        print "exec script error", repr(script)
        sys.stderr.write(traceback.format_exc())
    else:
        print "exec script end", repr(script)


def run_forever(args):
    """run script interactively in forever mode, to reduce env setup time"""
    while True:
        print "wait for stdin..."
        sys.stdout.flush()
        input_line = sys.stdin.readline().strip()
        print 'get input_line', input_line
        if input_line.startswith("c "):
            _, script, code = input_line.split(" ")
            code = unquote(code)  # decode code
            print "exec code %s" % repr(code)

            _exec_script_for_forever(args, script, code=code)
        elif input_line.startswith("f "):
            _, script = input_line.split(" ")
            script = input_line.strip()[2:]
            print "exec script %s" % repr(script)

            _exec_script_for_forever(args, script)
        elif input_line == "exit":
            print "end of stdin"
            sys.exit(0)
        else:
            print "invalid input %s" % repr(input_line)

        sys.stdout.flush()
        sys.stderr.flush()
