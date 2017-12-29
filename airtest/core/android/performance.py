#! /usr/bin/env python
# -*- coding: utf-8 -*-

import Queue
import re
import time
import threading
import json
import traceback
import functools
import sys
import subprocess
import copy
import os
import logging
from collections import defaultdict
from airtest.core.error import PerformanceError, AdbShellError
from airtest.core.utils import split_cmd, get_std_encoding, get_logger
from airtest.core.settings import Settings as ST

LOGGING = get_logger('performance')


def find_value(pattern, content):
    match = re.search(pattern, content)
    if match:
        return match.groupdict() or match.groups() or match.group()
    return ""


def pfmlog(func):
    """
    记录性能数据的装饰器，把返回值加上时间信息变成一条log，插入到结果队列中
    Parameters
    ----------
    func 调用的cpu/pss等方法

    Returns
    -------

    """
    @functools.wraps(func)
    def log_it(*args, **kwargs):
        log_time = getattr(args[0], 'collect_time', int(time.time())) if args[0] else int(time.time())
        try:
            data = func(*args)
        except Exception:
            data = {"name": "traceback", "value": traceback.format_exc(), "time": log_time}
            args[0].result_queue.put(data)
            if args[0].stop_event:
                args[0].stop_event.set()
            raise
        else:
            if data is None:
                # 读到的数据可能为0或者None, 0代表取到数据是0，但是None代表取不到数据/数据为空/数据异常，也记下来，用""来代替
                data = ""
            args[0].result_queue.put({"name": func.__name__, "value": json.dumps(data), "time": log_time})
        return data
    return log_it


def cmd_without_log(adb, cmds, device=True):
    """
    重写adb.shell里的start_cmd，把LOG屏蔽掉，避免刷屏
    Returns
    -------

    """
    cmds = split_cmd(cmds)
    cmd_options = adb.cmd_options
    if device:
        if not adb.serialno:
            raise RuntimeError("please set serialno first")
        cmd_options = cmd_options + ['-s', adb.serialno]
    cmds = cmd_options + cmds
    cmds = [c.encode(get_std_encoding(sys.stdin)) for c in cmds]

    proc = subprocess.Popen(
        cmds,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return proc


class Performance(object):
    def __init__(self, adb, package_name, log_file="pfm.txt", interval=2):
        """
        收集性能数据
        Parameters
        ----------
        adb ADB对象
        package_name 要收集数据的包名，获取到pid来进行数据收集，避免负载过大
        log_file 输出的log文件路径
        interval 间隔时间
        """
        # adb初始化
        self._init_adb(adb)
        self.package_name = package_name
        self.result_file = log_file
        self.interval = interval

        self.collector = None
        self.collector_thread = None
        self.stop_event = threading.Event()
        self.result = []
        self._init_collector()

    def _init_adb(self, adb):
        # adb初始化，由于需要屏蔽掉原先adb.shell中的log输出，所以需要另外copy一个adb对象专门在这里使用
        # threading.lock不能被deepcopy，需要另外单独取出来再进行复制
        lock = adb._display_info_lock
        adb._display_info_lock = None
        self.adb = copy.deepcopy(adb)
        adb._display_info_lock = lock
        # 把start_cmd替换成无log版本
        self.adb.start_cmd = functools.partial(cmd_without_log, self.adb)

    def _init_collector(self):
        # 初始化数据收集对象
        self.collector = Collector(self.adb, self.package_name, self.stop_event)
        with open(self.result_file, "w") as f:
            pass

    def start(self):
        # log级别设成INFO，不打出DEBUG级别的log
        LOGGING.setLevel(logging.INFO)
        # 最好等到已经启动应用后再开始数据收集
        if not self.collector_thread:
            if self.stop_event.is_set():
                self.stop_event.clear()
            self.collector_thread = threading.Thread(target=self.collect_data)
            self.collector_thread.setDaemon(True)
            self.collector_thread.start()
            LOGGING.info("begin data collection")

    def stop(self):
        if self.collector_thread:
            self.stop_event.set()
            self.collector_thread.join(3)
            self.collector_thread = None
            self.save_data()
            LOGGING.info("stop data collection")

    def start_forever(self):
        """
        命令行状态下，想要一直开着数据收集线程，又要支持用ctrl+c终止收集，逻辑跟普通的方式有点小区别
        Returns
        -------

        """
        # log级别设成debug，会定期打一些数据出来，方便在命令行下查看结果
        LOGGING.setLevel(logging.DEBUG)
        if not self.collector_thread:
            try:
                if self.stop_event.is_set():
                    self.stop_event.clear()
                self.collector_thread = threading.Thread(target=self.collect_data)
                self.collector_thread.start()
                LOGGING.info("begin data collection...")
                # 用这个方式来保证线程一直执行不中断...
                while True:
                    time.sleep(100)
            except (KeyboardInterrupt, SystemExit):
                print '\n! Received keyboard interrupt, quitting threads.\n'
                self.stop_event.set()
                sys.exit()
            except:
                print "\nexception occurred!\n"
                self.stop_event.set()
                raise

    def collect_data(self):
        """
        数据收集
        Returns
        -------

        """
        count = 0
        try:
            while not self.stop_event.is_set():
                if not self.collector.pid:
                    # 如果进程未启动，尝试去获取一下pid
                    self.collector.get_pid()
                thread_list = []
                # 用同一个时间作为数据记录时间，方便后期同步数据
                self.collector.collect_time = int(time.time())
                for method in self.collector.collect_method:
                    try:
                        t = threading.Thread(target=method)
                        t.setDaemon(True)
                        t.start()
                        thread_list.append(t)
                    except Exception:
                        self.stop_event.set()
                        self.save_data()
                        raise
                for t in thread_list:
                    t.join()
                count += 1
                if count % 5 == 0:
                    self.save_data()
                time.sleep(self.interval)
            self.save_data()
        except Exception:
            LOGGING.error("stop collection thread")
            LOGGING.error(traceback.format_exc())
            if self.stop_event:
                self.stop_event.set()
            if self.collector:
                self.collector.result_queue.put({"name": "traceback", "value": traceback.format_exc(), "time": int(time.time())})
                self.save_data()

    def save_data(self):
        # 把收集到的数据先放在队列里，取出来之后再写入log文件
        if not self.collector:
            LOGGING.error("Collect data failed.")
            return []
        while not self.collector.result_queue.empty():
            self.result.append(self.collector.result_queue.get())
        result = self.result
        self.result = []
        LOGGING.debug(repr(result))
        try:
            with open(self.result_file, "a") as f:
                for i in result:
                    try:
                        text = json.dumps(i)
                    except TypeError:
                        text = repr(i)
                    f.write(text)
                    f.write("\n")
        except:
            LOGGING.error("Saving data failed!", repr(result))
            raise
        return result

    def read_data(self):
        try:
            with open(self.result_file, "r") as f:
                data = f.read()
        except:
            LOGGING.error("Open log file failed!")
            raise
        return data


class Collector(object):
    """ 收集数据专用 """
    def __init__(self, adb, package_name, stop_event=None):
        self.collect_method = [self.pss, self.cpu, self.net_flow, self.cpu_freq]
        self.result_queue = Queue.Queue()
        self.adb = adb
        self.package_name = package_name
        self._pid = None
        self._uid = ""
        self._sdk_version = adb.sdk_version
        self._cpu_kernel = self.cpu_kel()

        self.collect_time = int(time.time())
        self.prev_temp_data = defaultdict(dict)
        self.stop_event = stop_event

    @property
    def pid(self):
        return self._pid

    def _init_data(self):
        """
        重启app之后可能需要重置数据
        Returns
        -------

        """
        self.get_pid()
        self._uid = ""
        self.prev_temp_data = defaultdict(dict)

    def get_pid(self):
        output = self.adb.shell("dumpsys meminfo {package_name}".format(package_name=self.package_name))
        get_pid = find_value(r"pid (?P<pid>\d+)", output)
        if get_pid and get_pid.get("pid"):
            self._pid = get_pid.get("pid")
            return self._pid

    @pfmlog
    def pss(self):
        """
        USS	Unique Set Size	物理内存	进程独占的内存
        PSS	Proportional Set Size	物理内存	PSS= USS+ 按比例包含共享库
        RSS	Resident Set Size	物理内存	RSS= USS+ 包含共享库
        VSS	Virtual Set Size	虚拟内存	VSS= RSS+ 未分配实际物理内存

        此处取pss,单位是KB
        Returns
        -------

        """
        output = self.adb.shell("dumpsys meminfo {package_name}".format(package_name=self.package_name))
        get_pss = find_value(r"[Tt][Oo][Tt][Aa][Ll]\s+(?P<pss>\d+)", output)
        if get_pss:
            return get_pss.get("pss")
        else:
            return None

    def battery(self):
        """
        当前电量获取
        Returns
        -------

        """
        output = self.adb.shell("dumpsys battery")
        get_level = find_value(r"[Ll][Ee][Vv][Ee][Ll][\s\:]*(?P<level>\d+)", output)
        if get_level:
            return get_level.get("level")
        return None

    def cpu_kel(self):
        """
        cpu核心数量的获取
        Returns
        -------

        """
        output = self.adb.shell("cat /proc/cpuinfo")
        return len(re.findall("processor", output))

    def total_cpu_time(self):
        """
        user:从系统启动开始累计到当前时刻，处于用户态的运行时间，不包含 nice值为负进程。
        nice:从系统启动开始累计到当前时刻，nice值为负的进程所占用的CPU时间
        system 从系统启动开始累计到当前时刻，处于核心态的运行时间
        idle 从系统启动开始累计到当前时刻，除IO等待时间以外的其它等待时间
        iowait 从系统启动开始累计到当前时刻，IO等待时间(since 2.5.41)
        irq 从系统启动开始累计到当前时刻，硬中断时间(since 2.6.0-test4)
        softirq 从系统启动开始累计到当前时刻，软中断时间(since 2.6.0-test4)
        stealstolen  这是时间花在其他的操作系统在虚拟环境中运行时（since 2.6.11）
        guest 这是运行时间guest 用户Linux内核的操作系统的控制下的一个虚拟CPU（since 2.6.24）
        """
        output = self.adb.shell("cat /proc/stat")
        res = output.split()
        line = output.split("\n")[0].split()

        for info in res:
            if info.decode() == "cpu":
                user = res[1].decode()
                nice = res[2].decode()
                system = res[3].decode()
                idle = res[4].decode()
                if len(line) >= 8:
                    iowait = res[5].decode()
                    irq = res[6].decode()
                    softirq = res[7].decode()
                    result = int(user) + int(nice) + int(system) + int(idle) + int(iowait) + int(irq) + int(softirq)
                else:
                    result = int(user) + int(nice) + int(system) + int(idle)
                return result

    def process_cpu_time(self):
        """
        pid     进程号
        utime   该任务在用户态运行的时间，单位为jiffies
        stime   该任务在核心态运行的时间，单位为jiffies
        cutime  所有已死线程在用户态运行的时间，单位为jiffies
        cstime  所有已死在核心态运行的时间，单位为jiffies
        """
        if not self.pid:
            return None
        # 如果获取不到pid相关的数据，说明已经没有在运行，返回0或者抛出异常
        try:
            output = self.adb.shell("cat /proc/{pid}/stat".format(pid=self.pid))
            assert len(output) != 0
        except (AdbShellError, AssertionError):
            LOGGING.error("No such file: /proc/{pid}/stat".format(pid=self.pid))
            self._init_data()
            return None
        res = output.split()
        if len(res) < 17:
            raise PerformanceError("Get process cpu time failed! data: " + repr(res))
        utime = res[13].decode()
        stime = res[14].decode()
        cutime = res[15].decode()
        cstime = res[16].decode()
        result = int(utime) + int(stime) + int(cutime) + int(cstime)
        return result

    @pfmlog
    def cpu(self):
        return self.cpu_cal()

    def cpu_cal(self):
        """
        CPU使用率的计算
        1．采样两个足够短的时间间隔的cpu快照与进程快照，
        a) 每一个cpu快照均为(user、nice、system、idle、iowait、irq、softirq、stealstolen、guest)的9元组;
        b) 每一个进程快照均为 (utime、stime、cutime、cstime)的4元组；
        2．计算出两个时刻的总的cpu时间与进程的cpu时间，分别记作：totalCpuTime1、totalCpuTime2、processCpuTime1、processCpuTime2
        3．计算该进程的cpu使用率pcpu = 100*( processCpuTime2 – processCpuTime1) / (totalCpuTime2 – totalCpuTime1) (按100%计算，如果是多核情况下还需乘以cpu的个数);

        这里取时间片=0.1s，计算结果如果为负就重新再取，尝试5次，返回结果除以核心数*100%，取小数点后2位
        Returns
        -------

        """
        count = 5
        while count > 0:
            process_cpu_time1 = self.process_cpu_time()
            if not process_cpu_time1:
                return None
            total_cpu_time1 = self.total_cpu_time()

            time.sleep(0.1)
            process_cpu_time2 = self.process_cpu_time()
            if not process_cpu_time2:
                return None
            total_cpu_time2 = self.total_cpu_time()
            dt_process_time = process_cpu_time2 - process_cpu_time1
            dt_total_time = total_cpu_time2 - total_cpu_time1

            cpu = round(100 * ((dt_process_time * 1.0) / dt_total_time), 2)
            if cpu < 0.001:
                LOGGING.error("cpu data error: %s, %s" % (str(total_cpu_time1), str(total_cpu_time2)))
                count -= 1
                continue
            ret = round(cpu/self._cpu_kernel, 2)
            if ret > 100:
                LOGGING.error("cpu data error: %s, %s, %s, %s" % (str(total_cpu_time1), str(total_cpu_time2),
                                                                  str(dt_total_time), str(dt_process_time)))
                continue
            return ret
        return None

    def cpu_info(self):
        """
        用dumpsys cpuinfo的指令获取cpu占用率，需要除以cpu核心数，而且数值的更新较慢
        Returns
        -------

        """
        output = self.adb.shell("dumpsys cpuinfo")
        cpu_usage = find_value(r"(?P<usage>\d+)%\s*"+str(self.pid) + "\/", output)
        return cpu_usage["usage"] if cpu_usage else None

    def cpu_top(self):
        """
        用top指令去获取cpu占用率，速度最慢
        Returns
        -------

        """
        output = self.adb.shell("top -n 1")
        cpu_usage = find_value(r"{pid}\s+\d+\s+(?P<usage>\d+)%\s+".format(pid=str(self.pid)), output)
        return cpu_usage["usage"] if cpu_usage else None

    def uid(self):
        if self._uid:
            return self._uid
        if self.pid:
            try:
                output = self.adb.shell("cat /proc/{pid}/status".format(pid=self.pid))
            except AdbShellError:
                return ""
            get_uid = find_value(r"[Uu]id[\s\:]*(?P<uid>\d+)", output)
            if get_uid:
                if get_uid and get_uid.get("uid"):
                    self._uid = get_uid.get("uid")
                    return self._uid
        return ""

    @pfmlog
    def net_flow(self):
        """
        上下行流量
        Returns (当前流量 - 上一个时间点的流量) / (时间差)  = n B/s
        -------

        """
        uid = self.uid()
        if uid:
            output = self.adb.shell("cat /proc/net/xt_qtaguid/stats")
            rx_bytes = 0
            tx_bytes = 0
            for line in output.split("\n"):
                if uid in line:
                    bytes = line.split()
                    rx_bytes += int(bytes[5])
                    tx_bytes += int(bytes[7])
            prev_net_flow = self.prev_temp_data['net']
            ret = rx_bytes + tx_bytes
            if not prev_net_flow:
                self.prev_temp_data['net'] = {'bytes': ret, 'time': self.collect_time}
                return None
            else:
                self.prev_temp_data['net'] = {'bytes': ret, 'time': self.collect_time}
                if self.collect_time != prev_net_flow['time']:
                    # 流量/时间
                    return round((ret - prev_net_flow['bytes'])*1.0 / (self.collect_time - prev_net_flow['time']), 2)
                else:
                    return ret - prev_net_flow['bytes']
        return None

    @pfmlog
    def cpu_freq(self):
        ret = defaultdict(lambda: "0")

        def cur_freq(i):
            online = self.adb.shell("cat /sys/devices/system/cpu/cpu%s/online" % str(i))
            if "1" in online:
                try:
                    cpu = self.adb.shell("cat /sys/devices/system/cpu/cpu%s/cpufreq/scaling_cur_freq" % str(i)).strip()
                    ret[i] = cpu if cpu.isdigit() else "0"
                except AdbShellError:
                    ret[i] = "0"
            else:
                ret[i] = "0"

        t_list = []
        for i in range(0, self._cpu_kernel):
            t = threading.Thread(target=cur_freq, args=(i,))
            t_list.append(t)
            t.start()
        for t in t_list:
            t.join()
        return ret


# 命令行启动性能数据收集
def pfm_parger(ap):
    """
    命令行运行参数
    运行范例： 本地设备python -m airtest performance com.netease.my --outfile pfm.txt --setsn xxx(只有一台可不写）
    远程设备用uri访问：
    python -m airtest performance com.netease.my --device android://10.250.199.230:5039/0815f8485f032404

    Parameters
    ----------
    ap

    Returns
    -------

    """
    ap.add_argument("package", help="package name")
    ap.add_argument("--device", help="set dev by url string", nargs="?", const="")
    ap.add_argument("--setsn", help="set dev by serialno", nargs="?", const="")
    ap.add_argument("--outfile", help="output performance log file ", default="pfm.txt")
    return ap


def init_device_uri(uri):
    from urlparse import urlparse, parse_qsl
    d = urlparse(uri)
    platform = d.scheme
    host = d.netloc
    uuid = d.path.lstrip("/")
    params = dict(parse_qsl(d.query))
    if platform != "android":
        raise RuntimeError("unsupported platform")
    if host:
        params["adbhost"] = host.split(":")
    return init_device_serialno(uuid, **params)


def init_device_serialno(serialno=None, adbhost=None):
    from airtest.core.android.adb import ADB
    if not serialno:
        serialno = ADB().devices(state="device")[0][0]
    adb = ADB(serialno, server_addr=adbhost)
    adb.wait_for_device()
    return adb


def performance_main(args):
    package_name = args.package
    if not package_name:
        raise PerformanceError("package name is required!")
    if args.setsn:
        adb = init_device_serialno(args.setsn)
    elif args.device:
        adb = init_device_uri(args.device)
    else:
        adb = init_device_serialno()
    log_file = args.outfile if args.outfile else "pfm.txt"
    pfm = Performance(adb, package_name, log_file=log_file)
    pfm.start_forever()


def save_extra_data(data, filename="fps.txt"):
    """
    临时增加的新接口，用于写一些引擎专用的数据到文件中
    Parameters
    ----------
    data: [{data..}]

    Returns
    -------

    """
    log_file = os.path.join(ST.LOG_DIR, "fps.txt" if ST.LOG_DIR else filename)
    print("write data", log_file)
    with open(log_file, "a") as f:
        data = json.dumps(data)
        f.write(data)
        f.write("\r\n")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    args = pfm_parger(ap).parse_args()

    performance_main(args)
