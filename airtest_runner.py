import os
import argparse
# import here to build dependent modules
from moa.moa import *

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="script filename")
    ap.add_argument("--utilfile", help="utils filepath to implement your own funcs")
    ap.add_argument("--setsn", help="auto set serialno", action="store_true")
    ap.add_argument("--log", help="auto set log file", nargs="?", const="log.txt")
    ap.add_argument("--screen", help="auto set screen dir", nargs="?", const="img_record")
    args = ap.parse_args()

    # reading code from file
    code = open(args.script).read()

    # loading util file
    if args.utilfile:
        if os.path.isfile(args.utilfile):
            print "try loading:", args.utilfile
            utilcontent = open(args.utilfile).read()
            exec(utilcontent)
        else:
            print "file does not exist:", os.path.abspath(args.utilfile)

    # cd script dir
    os.chdir(os.path.dirname(args.script))

    if args.setsn:
        print "auto set_serialno"
        set_serialno()

    if args.log:
        print "save log in", args.log
        set_logfile(args.log)

    if args.screen:
        print "save img in", args.screen
        set_screendir(args.screen)

    # execute code
    exec(code)


if __name__ == '__main__':
    main()
