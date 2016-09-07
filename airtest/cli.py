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


def exec_script(scriptname, scriptext=".owl", tplext=".png", scope=None, original=False, pyfilename=None):
    """
    execute script: original or submodule
    1. cd to original dir
    2. exec original script
    3. if sub:
        2.1 cp imgs to sub_dir
        2.2 set_basedir(sub_dir)
        2.3 exec sub script
        2.4 set_basedir(ori_dir)
    """
    if not original and not os.path.isabs(scriptname):
        if not SCRIPTHOME:
            raise RuntimeError("SCRIPTHOME not set, please set_scripthome first")
        scripthome = os.path.abspath(SCRIPTHOME)
        scriptpath = os.path.join(scripthome, scriptname)
    elif original:
        scriptpath = "."
    else:
        scriptpath = scriptname

    def copy_script(src, dst):
        if os.path.isdir(sub_dir):
            shutil.rmtree(dst, ignore_errors=True)
        os.mkdir(sub_dir)
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

    ori_dir = None
    # copy submodule's images into sub_dir, and set_basedir
    if not original:
        ori_dir = BASE_DIR
        sub_dir = get_sub_dir_name(scriptname)
        set_basedir(sub_dir)
        copy_script(scriptpath, sub_dir)

    # start to exec
    log("function", {"name": "exec_script", "step": "start"})
    print "exec_script", scriptpath
    if not pyfilename:
        pyfilename = os.path.basename(scriptname).replace(scriptext, ".py")
    pyfilepath = os.path.join(scriptpath, pyfilename)
    code = open(pyfilepath).read()
    if scope:
        exec(code) in scope
    else:
        exec(code) in globals()
    # set_basedir back to original dir
    if ori_dir:
        set_basedir(ori_dir)
    log("function", {"name": "exec_script", "step": "end"})
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
    """to be overwritten by uses"""
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="script filename")
    ap.add_argument("--utilfile", help="utils filepath to implement your own funcs")
    ap.add_argument("--pyfile", help="py filename to run in script dir, omit to be the same as script name", nargs="?", const=None)
    ap.add_argument("--setsn", help="set dev by serialno", nargs="?", const="")
    ap.add_argument("--setadb", help="set adb ip and port, default 127.0.0.1:5037 .")
    ap.add_argument("--setudid", help="set ios device udid", nargs="?", const="")
    ap.add_argument("--setwin", help="set dev by windows handle", nargs="?", const="")
    ap.add_argument("--devcount", help="set dev count autoly", nargs="?", const=1, default=1, type=int)
    ap.add_argument("--log", help="auto set log file", nargs="?", const="log.txt")
    ap.add_argument("--screen", help="auto set screen dir", nargs="?", const="img_record")
    ap.add_argument("--kwargs", help="extra kwargs")
    ap.add_argument("--forever", help="run forever, read stdin and exec", action="store_true")
    ap.add_argument("--findoutside", help="find outside a rectangle area.")
    ap.add_argument("--setemulator", help="set emulator name default bluestacks", nargs="?", const=True)

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

    if args.findoutside:
        set_find_outside(args.findoutside)

    if args.setsn is not None:
        print "set_serialno", args.setsn
        if args.setadb:
            addr = args.setadb.split(":")
        else:
            addr = None
        if args.setsn == "":
            for i in range(args.devcount):
                # auto choose one serialno
                set_serialno(addr=addr)
        else:
            for sn in args.setsn.split(","):
                set_serialno(sn, addr=addr)
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

    if args.kwargs:
        print "load kwargs", repr(args.kwargs)
        for kv in args.kwargs.split(","):
            k, v = kv.split("=")
            globals()[k] = v

    if args.setemulator:
        print "set_emulator", args.setemulator #  add by zq
        emu_name = args.setemulator if isinstance(args.setemulator, str) else None
        if args.setadb:
            addr = args.setadb.split(":")
            set_emulator(emu_name, addr=addr)
        else:
            set_emulator(emu_name)

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
                        
                    exec_script(script, scope=globals(), original=True, pyfilename=pyfile)
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

    exit_code = 0

    for script in args.script.split(","):
        # cd script dir
        os.chdir(script)

        if args.log:
            print "save log in", "'%s'" %args.log
            set_logfile(args.log)

        if args.screen:
            print "save img in", "'%s'" %args.screen
            set_screendir(args.screen)

        _on_init_done()

        try:
            # execute code
            set_current(0)
            exec_script(script, scope=globals(), original=True, pyfilename=args.pyfile)
        except Exception:
            traceback.print_exc()
            exit_code = 1

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
