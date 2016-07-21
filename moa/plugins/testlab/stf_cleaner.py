from stf_runner import *
import time
import subprocess
import traceback
import threading


def run_on_all_devices():
    for sn in devices():
        def func(sn):
            try:
                addr = join(sn)
                dev = Android(addr, init_display=False, minicap=False, minitouch=False, init_ime=False)
                # home
                # dev.home()

                # turn screen red to find device
                print dev.shell(['am', 'start', '-a', 'jp.co.cyberagent.stf.ACTION_IDENTIFY'])

                # shine
                # for i in range(100):
                #     dev.home()
                #     print dev.shell(['am', 'start', '-a', 'jp.co.cyberagent.stf.ACTION_IDENTIFY'])
                #     time.sleep(1)
                
            except:
                traceback.print_exc()
            finally:
                cleanup(sn)
        t = threading.Thread(target=func, args=(sn, ))
        t.start()


if __name__ == '__main__':
    run_on_all_devices()
