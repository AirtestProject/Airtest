from airtest.moa.moa import *
import os
import sys
import argparse
# import here to build dependent modules
import g1utils
import g18utils
ap = argparse.ArgumentParser()
ap.add_argument("script", help="script filename")
ap.add_argument("libdir", help="utils libdir")
ap.add_argument("--setsn", help="auto set serialno", action="store_true")
ap.add_argument("--log", help="auto set log file", nargs="?", const="log.txt")
ap.add_argument("--screen", help="auto set screen dir", nargs="?", const="img_record")
args = ap.parse_args()

# reading code from file
code = open(args.script).read()

# loading extra libs
utilfile = os.path.join(args.libdir, "utils.py")
if os.path.isfile(utilfile):
    print "try loading:", utilfile
    utilcontent = open(utilfile).read()
    exec(utilcontent)
else:
    print "file does not exist:", os.path.abspath(utilfile)

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
