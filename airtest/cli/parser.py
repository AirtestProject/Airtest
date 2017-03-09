# -*- coding: utf-8 -*-
# @Author: gzliuxin
# @Email:  gzliuxin@corp.netease.com
# @Date:   2017-03-09 11:48:48


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="script filename")
    ap.add_argument("--getinfo", help="get script info, like __author__ __title__ __desc__", action="store_true")
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

    # get script info, and print to stdout:
    if args.getinfo:
        json_info = get_script_info(args.script)
        print json_info
        return

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
                set_find_outside(v)
            else:
                globals()[k] = v

    # run script in forever mode, read input & exec
    if args.forever:
        forever_handle(args)

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
    # SCRIPT_STACK.append(args.script)
    try:
        # execute pre script
        if args.pre:
            set_basedir(args.pre)
            for i in range(len(DEVICE_LIST)):  # pre for all devices
                set_current(i)
                exec_script(args.pre, scope=globals(), root=True)

        # execute script
        set_basedir(args.script)
        set_current(0)
        exec_script(args.script, scope=globals(), root=True)
    except:
        err = traceback.format_exc()
        log("error", {"script_exception": err})
        raise
    finally:
        # execute post script, whether pre & script succeed or not
        if args.post:
            try:
                set_basedir(args.post)
                for i in range(len(DEVICE_LIST)):  # post for all devices
                    set_current(i)
                    exec_script(args.post, scope=globals(), root=True)
            except:
                log("error", {"post_exception": traceback.format_exc()})
                traceback.print_exc()

if __name__ == '__main__':
	main()
