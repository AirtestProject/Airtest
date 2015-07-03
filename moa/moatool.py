# coding: utf-8

import urllib
import sys
import argparse
import moa

def new_argparser():
    parser = argparse.ArgumentParser(description='Tool to run and make moa script')
    parser.add_argument('-s', '--serialno', dest='serialno', type=str, required=True, help='Serial Number of device')

    sub = parser.add_subparsers(dest='action')
    prun = sub.add_parser('run')
    prun.add_argument('-b', '--root', dest='root', default='.', type=str, help='Root dir to find pic and store log')
    prun.add_argument('script', action='store', type=str)

    pss = sub.add_parser('snapshot')
    pss.add_argument('-p', '--png', dest='png', type=str, help='Save output png file')
    return parser
    
# exec_script(script.decode('string-escape'))
def main():
    parser = new_argparser()
    res = parser.parse_args(sys.argv[1:])
    #print res
    moa.set_serialno(res.serialno)
    if res.action == 'run':
        moa.set_basedir(res.root)
        moa.exec_script(urllib.unquote(res.script))

    if res.action == 'snapshot':
        if res.png:
            moa.snapshot(res.png)
            print 'Saved success'
            return
        screen = moa.snapshot()
        import cv2
        import numpy as np
        nparr = np.fromstring(screen, np.uint8)
        img = cv2.imdecode(nparr, cv2.CV_LOAD_IMAGE_COLOR)
        cv2.namedWindow('dst_rt', cv2.WINDOW_NORMAL)
        cv2.imshow('dst_rt', img)
        cv2.waitKey(0)
        #cv2.namedWindow('dst', cv2.CV_WINDOW_AUTOSIZE);
        #cv2.resizeWindow('dst_rt', window_width, window_height)

        cv2.destroyAllWindows()
    # serialno, base_dir, script = sys.argv[1: 4]
    # # # print sys.argv[1: 4]
    # moa.set_serialno(serialno)
    # moa.set_basedir(base_dir)
    # moa.exec_script(urllib.unquote(script))

if __name__ == '__main__':
    main()
