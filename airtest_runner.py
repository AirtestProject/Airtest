# -*- coding: utf-8 -*-

import os
import json
import argparse
from moa.moa import *
# import here to build dependent modules
import requests
import re
import urllib2
import time
import sdkautomator


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
        if not os.path.isdir(sub_dir):
            os.mkdir(sub_dir)
        # copy_script(scriptpath, sub_dir)
        try:
            copy_script(scriptpath, sub_dir)
        except:
            log("error", {"name": "exec_script", "step": "fail","args": ["   "+scriptpath+ "   "], "traceback": "Fail to find this child script.."}, False)
            return scriptpath

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="script filename")
    ap.add_argument("--utilfile", help="utils filepath to implement your own funcs")
    ap.add_argument("--pyfile", help="py filename to run in script dir, omit to be the same as script name", nargs="?", const=None)
    ap.add_argument("--setsn", help="auto set serialno", nargs="?", const=True)
    ap.add_argument("--setudid", help="auto set ios device udid", nargs="?", const=True)
    ap.add_argument("--setwin", help="auto set windows", action="store_true")
    ap.add_argument("--log", help="auto set log file", nargs="?", const="log.txt")
    ap.add_argument("--screen", help="auto set screen dir", nargs="?", const="img_record")
    ap.add_argument("--kwargs", help="extra kwargs")
    ap.add_argument("--forever", help="run forever, read stdin and exec", action="store_true")
    # 建军添加：设置运行进程中moa的参数，将maskrect设置为
    ap.add_argument("--maskrect", help="set IDE rect tobe a moa mask, during windows running.")

    args = ap.parse_args()

    # loading util file
    if args.utilfile:
        if os.path.isfile(args.utilfile):
            print "try loading:", args.utilfile
            utilcontent = open(args.utilfile).read()
            exec(utilcontent) in globals()
        else:
            print "file does not exist:", os.path.abspath(args.utilfile)

    # cd script dir
    os.chdir(args.script)

    # 建军添加2016-4-1：
    if args.maskrect:
        print "auto set mask_rect : ", args.maskrect
        set_mask_rect(args.maskrect)

    if args.setsn:
        print "auto set_serialno", args.setsn
        # if setsn==True, but not specified, auto choose one
        sn = args.setsn if isinstance(args.setsn, str) else None
        set_serialno(sn)

    if args.setudid:  # modified by gzlongqiumeng
        print "auto set_ios_udid", args.setudid
        udid = args.setudid if isinstance(args.setudid,str) else None
        set_ios_udid(udid)

    if args.setwin:
        print "auto set_windows"
        set_windows()

    if args.log:
        print "save log in", args.log
        set_logfile(args.log)

    if args.screen:
        print "save img in", args.screen
        set_screendir(args.screen)

    if args.kwargs:
        print "load kwargs", repr(args.kwargs)
        for kv in args.kwargs.split(","):
            k, v = kv.split("=")
            globals()[k] = v

    if args.forever:
        while True:
            print "wait for stdin..."
            sys.stdout.flush()
            line = sys.stdin.readline()
            exec(line) in globals()
            if line == "":
                print "end of stdin"
                exit(0)
            pass

    # execute code
    exec_script(args.script, scope=globals(), original=True, pyfilename=args.pyfile)


if __name__ == '__main__':
    main()
