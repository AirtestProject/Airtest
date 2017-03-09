#!/usr/bin/env
# -*- coding: utf-8 -*-

import time
import os
import sys
import json
import argparse
import traceback
import core.main
from urllib import unquote
from core.main import *
from core.error import MinicapError, MinitouchError, AdbError
from core.utils.script_info_utils import get_script_info
# import here to build dependent modules
import requests
import re
import urllib2

SCRIPT_STACK = []

# def _is_root_script(scriptname):
#     return scriptname == args.script

def exec_script(scriptname, scriptext=".owl", tplext=".png", scope=None, root=False, code=None):
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

    # start exec
    log("function", {"name": "exec_script", "step": "start", "script": scriptname})
    print "script_stack", SCRIPT_STACK
    print "exec_script", scriptpath
    # read code
    if code is None:
        pyfilename = os.path.basename(scriptname).replace(scriptext, ".py")
        pyfilepath = os.path.join(scriptpath, pyfilename)
        code = open(pyfilepath).read()

    if not root:
        # copy submodule's images into sub_dir
        sub_dir = get_sub_dir_name(scriptname)
        sub_dirpath = os.path.join(SCRIPT_STACK[0], sub_dir)
        copy_script(scriptpath, sub_dirpath)
        # SCRIPT_STACK[-1] = sub_dir

        # replace tpl filepath with filepath in sub_dir
        code = re.sub("[\'\"](\w+.png)[\'\"]", "\"%s/\g<1>\"" % sub_dir, code)
    # exec code
    if scope:
        exec(compile(code, scriptname, 'exec')) in scope
    else:
        exec(compile(code, scriptname, 'exec')) in globals()
    # finish exec
    log("function", {"name": "exec_script", "step": "end", "script": scriptname})
    # if not _is_root_script(scriptname):
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


def _exec_script_for_forever(args, script, code=None):
    # IDE使用的文件路径被命令行下的编码处理过，需要解码
    try:
        charset = sys.stdin.encoding
        script = script.decode(charset)
    except:
        pass

    set_basedir(script)

    try:
        exec_script(script, scope=globals(), root=True, code=code)
    except (MinitouchError, MinicapError, AdbError) as e:
        raise e
    except:
        print "exec script error", repr(script)
        sys.stderr.write(traceback.format_exc())
    else:
        print "exec script end", repr(script)


def forever_handle(args):  # args先传着，有需要用到其他参数可以直接拓展，不想用全局变量- - 
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
