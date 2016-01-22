import os
import json
import argparse
# import here to build dependent modules
from moa.moa import *
import g1utils
import g18utils
import sdkautomator


def exec_script(scriptname, scriptext=".owl", tplext=".png", scope=None, original=False):
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
    if os.path.isabs(scriptname):
        scriptpath = scriptname
    else:
        scripthome = SCRIPTHOME or ".."
        scriptpath = os.path.join(scripthome, scriptname)
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
        if not os.path.isdir(BASE_DIR):
            os.mkdir(BASE_DIR)
        copy_script(scriptpath, BASE_DIR)
    # start to exec
    log("function", {"name": "exec_script", "step": "start"})
    print "exec_script", scriptpath
    pyfilename = os.path.basename(scriptpath).replace(scriptext, ".py")
    pyfilepath = os.path.join(scriptpath, pyfilename)
    code = open(pyfilepath).read()
    if scope:
        exec(code, scope, scope)
    else:
        exec(code) in globals()
    # set_basedir back
    if ori_dir:
        set_basedir(ori_dir)
    log("function", {"name": "exec_script", "step": "end"})
    return scriptpath


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="script filename")
    ap.add_argument("--utilfile", help="utils filepath to implement your own funcs")
    ap.add_argument("--setsn", help="auto set serialno", nargs="?", const=True)
    ap.add_argument("--setwin", help="auto set windows", action="store_true")
    ap.add_argument("--log", help="auto set log file", nargs="?", const="log.txt")
    ap.add_argument("--screen", help="auto set screen dir", nargs="?", const="img_record")
    ap.add_argument("--kwargs", help="extra kwargs")
    ap.add_argument("--forever", help="run forever, read stdin and exec", action="store_true")
    args = ap.parse_args()


    if args.forever:
        f = open("tmp", "w")
        while True:
            print "wait for stdin..."
            line = sys.stdin.readline()
            f.write(line)
            f.flush()
            exec(line) in globals()
            if line == "":
                print "end of stdin"
                exit(0)
            pass


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

    if args.setsn:
        print "auto set_serialno", args.setsn
        # if setsn==True, but not specified, auto choose one
        sn = args.setsn if isinstance(args.setsn, str) else None
        set_serialno(sn)

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

    # execute code
    exec_script(args.script, scope=globals(), original=True)


if __name__ == '__main__':
    main()
