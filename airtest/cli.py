# -*- coding: utf-8 -*-

import time
import os
import sys
import json
import argparse
import traceback
import core.main
from core.main import *
from core.error import MinicapError, MinitouchError, AdbError
# import here to build dependent modules
import requests
import re
import urllib2

SCRIPT_STACK = []

def _is_root_script(scriptname):
    return scriptname == args.script

def exec_script(scriptname, scriptext=".owl", tplext=".png", scope=None):
    """
    execute script: root or submodule
    1. exec root script
    2. if submodule script:
        2.1 cp imgs to sub_dir
        2.2 exec sub script
    """
    if _is_root_script(scriptname):
        scriptpath = scriptname
    elif os.path.isabs(scriptname):
        SCRIPT_STACK.append(scriptname)
        scriptpath = scriptname
    else:
        if not SCRIPTHOME:
            raise RuntimeError("SCRIPTHOME not set, please set_scripthome first")
        SCRIPT_STACK.append(scriptname)
        scripthome = os.path.abspath(SCRIPTHOME)
        scriptpath = os.path.join(scripthome, scriptname)

    def copy_script(src, dst):
        if os.path.isdir(dst):
            shutil.rmtree(dst, ignore_errors=True)
        os.mkdir(dst)
        for f in os.listdir(src):
            srcfile = os.path.join(src, f)
            if not (os.path.isfile(srcfile) and f.endswith(tplext)):
                continue
            dstfile = os.path.join(dst, f)
            shutil.copy(srcfile, dstfile)

    def get_sub_dir_name(scriptname):
        dirname = os.path.splitdrive(os.path.normpath(scriptname))[-1]
        dirname = dirname.strip(os.path.sep).replace(os.path.sep, "_").replace(scriptext, "_sub")
        return dirname

    # copy submodule's images into sub_dir
    if not _is_root_script(scriptname):
        sub_dir = get_sub_dir_name(scriptname)
        sub_dirpath = os.path.join(SCRIPT_STACK[0], sub_dir)
        copy_script(scriptpath, sub_dirpath)
        SCRIPT_STACK[-1] = sub_dir

    # start exec
    log("function", {"name": "exec_script", "step": "start", "script": scriptname})
    print "script_stack", SCRIPT_STACK
    print "exec_script", scriptpath
    # read code
    pyfilename = os.path.basename(scriptname).replace(scriptext, ".py")
    pyfilepath = os.path.join(scriptpath, pyfilename)
    code = open(pyfilepath).read()
    if not _is_root_script(scriptname):
        # replace tpl filepath with filepath in sub_dir
        code = re.sub("[\'\"](\w+.png)[\'\"]", "\"%s/\g<1>\"" % SCRIPT_STACK[-1], code)
    # exec code
    if scope:
        exec(code) in scope
    else:
        exec(code) in globals()
    # finish exec
    log("function", {"name": "exec_script", "step": "end", "script": scriptname})
    if not _is_root_script(scriptname):
        SCRIPT_STACK.pop()
    return scriptpath


def set_scripthome(dirpath):
    global SCRIPTHOME
    SCRIPTHOME = dirpath


def get_globals(key):
    return getattr(core.main, key)


def set_globals(key, value):
    setattr(core.main, key, value)


def device():
    return get_globals("DEVICE")


def _on_init_done():
    """to be overwritten by users"""
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="script filename")
    ap.add_argument("--utilfile", help="utils filepath to implement your own funcs")
    ap.add_argument("--setsn", help="set dev by serialno", nargs="?", const="")
    ap.add_argument("--setudid", help="set ios device udid", nargs="?", const="")
    ap.add_argument("--setwin", help="set dev by windows handle", nargs="?", const="")
    ap.add_argument("--setemulator", help="set emulator name default bluestacks", nargs="?", const=True)
    ap.add_argument("--devcount", help="set dev count autoly", nargs="?", const=1, default=1, type=int)
    ap.add_argument("--log", help="set log dir, default to be script dir", nargs="?", const=True)
    ap.add_argument("--kwargs", help="extra kwargs")
    ap.add_argument("--forever", help="run in forever mode, read stdin and exec", action="store_true")
    ap.add_argument("--pre", help="run before script, setup environment")
    ap.add_argument("--post", help="run after script, clean up environment, will be run whether script succeeded or not")

    global args
    args = ap.parse_args()

    # loading util file
    if args.utilfile:
        if os.path.isfile(args.utilfile):
            print "try loading:", args.utilfile
            sys.path.append(os.path.dirname(args.utilfile))
            utilcontent = open(args.utilfile).read()
            exec(utilcontent) in globals()
        else:
            print "file does not exist:", os.path.abspath(args.utilfile)

    if args.setsn is not None:
        print "set_serialno", args.setsn
        if args.setsn == "":
            for i in range(args.devcount):
                # auto choose one serialno
                set_serialno()
        else:
            for sn in args.setsn.split(","):
                set_serialno(sn)
        set_current(0)

    if args.setudid is not None:  # modified by gzlongqiumeng
        print "set_udid", args.setudid
        udid = args.setudid if isinstance(args.setudid,str) else None
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
        print "set_emulator", args.setemulator #  add by zq
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
            globals()[k] = v

    # run script in forever mode, read input & exec
    if args.forever:
        while True:
            print "wait for stdin..."
            sys.stdout.flush()
            input_line = sys.stdin.readline()
            if input_line.startswith("c "):
                code = input_line.strip()[2:]
                print "exec code %s" % repr(code)
                try:
                    exec(code) in globals()
                except (MinitouchError,MinicapError,AdbError) as e:
                    raise e
                except:
                    print "exec code error"
                    sys.stderr.write(traceback.format_exc())
                else:
                    print "exec code end"
            elif input_line.startswith("f "):
                # print 'get input_line',input_line
                script = input_line.strip()[2:]
                pyfile = ""
                if script.endswith(".py"):
                    script,pyfile = os.path.split(script)
                print "exec script %s" % repr(script)
                # IDE使用的文件路径被命令行下的编码处理过，需要解码
                try:
                    charset = sys.stdin.encoding
                    script = script.decode(charset)
                except:
                    script = script
                try:
                    os.chdir(script)
                    if args.log:
                        print "save log in", "'%s'" %args.log
                        set_logfile(args.log)

                    if args.screen:
                        print "save img in", "'%s'" %args.screen
                        set_screendir(args.screen)
                        
                    exec_script(script, scope=globals())
                except (MinitouchError,MinicapError,AdbError) as e:
                    raise e
                except:
                    print "exec script error", repr(script)
                    sys.stderr.write(traceback.format_exc())
                else:
                    print "exec script end", repr(script)
            elif input_line == "":
                print "end of stdin"
                sys.exit(0)
            else:
                print "invalid input %s" % repr(input_line)
            sys.stdout.flush()
            sys.stderr.flush()

    # run script
    if args.log is True:
        print "save log & screen in script dir"
        set_logdir(args.script)
    elif args.log:
        print "save log & screen in '%s'" % args.log
        set_logdir(args.log)
    else:
        print "do not save log & screen"

    _on_init_done()
    # set root script as basedir
    set_basedir(args.script)
    SCRIPT_STACK.append(args.script)
    try:
        set_current(0)
        # execute pre script
        if args.pre:
            exec_script(args.pre, scope=globals())
        # execute script
        exec_script(args.script, scope=globals())
    except:
        err = traceback.format_exc()
        log("error", {"script_exception": err})
        raise
    finally:
        # execute post script, whether pre & script succeed or not
        if args.post:
            try:
                exec_script(args.post, scope=globals())
            except:
                log("error", {"post_exception": traceback.format_exc()})
                traceback.print_exc()


if __name__ == '__main__':
    main()
