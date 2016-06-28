from pprint import pprint
import stf
import sys


def run(serialno):
    stf.remote_disconnect(serialno)
    stf.leave_group(serialno)


if __name__ == '__main__':
    serialno = sys.argv[1]
    run(serialno)
