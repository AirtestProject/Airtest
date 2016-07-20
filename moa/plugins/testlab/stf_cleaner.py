from stf_runner import *


def run_on_all_devices():
    import subprocess
    import traceback
    for sn in devices():
        try:
            print subprocess.check_output("adb -s %s shell input keyevent HOME" % sn, shell=True)
            addr = join(sn)
            dev = Android(addr, init_display=False, minicap=False, minitouch=False, init_ime=False)
            # turn screen red to find device
            print dev.shell(['am', 'start', '-a', 'jp.co.cyberagent.stf.ACTION_IDENTIFY'])
        except:
            traceback.print_exc()
        finally:
            cleanup(sn)


if __name__ == '__main__':
    run_on_all_devices()
