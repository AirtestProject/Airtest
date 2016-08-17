import jenkinscli
import stf


def run_one_device(serialno):
    jenkinscli.build_job(serialno)


def run_multi_devices(sns):
    for sn in sns:
        run_one_device(sn)


def run_random_devices(count):
    listDevices = stf.get_device_list_rest()
    total = len(listDevices) 
    print "Available devices:", total
    if count is None:
        count = total
    elif count > total:
        print "warning: not enough devices(%s/%s), run on all" % (total, count)
        count = total

    for i in range(count):
        serialno = listDevices[i]['serial']
        print serialno
        run_one_device(serialno)


if __name__ == '__main__':
    run_random_devices(60)
