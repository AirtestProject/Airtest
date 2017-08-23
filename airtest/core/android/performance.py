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
from collections import defaultdict
from airtest.core.error import PerformanceError, AdbShellError
from airtest.core.utils import split_cmd, get_std_encoding, get_logger

LOGGING = get_logger('performance')


def find_value(pattern, content):
    match = re.search(pattern, content)
    if match:
        return match.groupdict() or match.groups() or match.group()
    return ""


def pfmlog(func):
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
            if data is not None:
                # 读到的数据可能为0或者None, 0也要记录下来，但是None不需要记录
                args[0].result_queue.put({"name": func.__name__, "value": data, "time": log_time})
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
        self._pid = ""
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
        # 初始化数据收集对象，但是要先获取到对应的pid才能开始收集数据
        self.pid()
        if self._pid:
            self.collector = Collector(self.adb, self.package_name, self._pid, self.stop_event)
            with open(self.result_file, "w") as f:
                pass

    def start(self):
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

    def collect_data(self):
        """
        数据收集
        Returns
        -------

        """
        count = 0
        failure_count = 0
        try:
            while not self.stop_event.is_set():
                # 在开始获取数据前，保证进程已启动
                if not self._pid:
                    if failure_count > 20:
                        raise PerformanceError("Please start app first")
                    self._init_collector()
                    if not self._pid:
                        failure_count += 1
                        time.sleep(1)
                    continue
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

    def pid(self):
        output = self.adb.shell("dumpsys meminfo {package_name}".format(package_name=self.package_name))
        get_pid = find_value(r"pid (?P<pid>\d+)", output)
        if get_pid and get_pid.get("pid"):
            self._pid = get_pid.get("pid")
            return self._pid


class Collector(object):
    """ 收集数据专用 """
    def __init__(self, adb, package_name, pid, stop_event=None):
        self.collect_method = [self.pss, self.cpu, self.net_flow]
        self.result_queue = Queue.Queue()
        self.adb = adb
        self.package_name = package_name
        self._pid = pid
        self._uid = ""

        self.collect_time = int(time.time())
        self.prev_temp_data = defaultdict(dict)
        self.stop_event = stop_event

    def _init_data(self):
        """
        重启app之后可能需要重置数据
        Returns
        -------

        """
        self.pid()
        self.prev_temp_data = defaultdict(dict)

    def pid(self):
        output = self.adb.shell("dumpsys meminfo {package_name}".format(package_name=self.package_name))
        get_pid = find_value(r"pid (?P<pid>\d+)", output)
        if get_pid and get_pid.get("pid"):
            self._pid = get_pid.get("pid")
            return self._pid

    @pfmlog
    def pss(self):
        output = self.adb.shell("dumpsys meminfo {package_name}".format(package_name=self.package_name))
        get_pss = find_value(r"[Tt][Oo][Tt][Aa][Ll]\s+(?P<pss>\d+)", output)
        if get_pss:
            return get_pss.get("pss")
        else:
            return ""

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
        return ""

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

        for info in res:
            if info.decode() == "cpu":
                user = res[1].decode()
                nice = res[2].decode()
                system = res[3].decode()
                idle = res[4].decode()
                iowait = res[5].decode()
                irq = res[6].decode()
                softirq = res[7].decode()
                result = int(user) + int(nice) + int(system) + int(idle) + int(iowait) + int(irq) + int(softirq)
                print "total_cpu_time: ", result, repr(output.split("\n")[0])
                return result

    def process_cpu_time(self):
        """
        pid     进程号
        utime   该任务在用户态运行的时间，单位为jiffies
        stime   该任务在核心态运行的时间，单位为jiffies
        cutime  所有已死线程在用户态运行的时间，单位为jiffies
        cstime  所有已死在核心态运行的时间，单位为jiffies
        """
        # 如果获取不到pid相关的数据，说明已经没有在运行，返回0或者抛出异常
        try:
            output = self.adb.shell("cat /proc/{pid}/stat".format(pid=self._pid))
        except AdbShellError:
            LOGGING.error("No such file: /proc/{pid}/stat".format(pid=self._pid))
            self._init_data()
            return 0
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
        """
        CPU使用率的计算
        1．采样两个足够短的时间间隔的cpu快照与进程快照，
        a) 每一个cpu快照均为(user、nice、system、idle、iowait、irq、softirq、stealstolen、guest)的9元组;
        b) 每一个进程快照均为 (utime、stime、cutime、cstime)的4元组；
        2．计算出两个时刻的总的cpu时间与进程的cpu时间，分别记作：totalCpuTime1、totalCpuTime2、processCpuTime1、processCpuTime2
        3．计算该进程的cpu使用率pcpu = 100*( processCpuTime2 – processCpuTime1) / (totalCpuTime2 – totalCpuTime1) (按100%计算，如果是多核情况下还需乘以cpu的个数);
        Returns
        -------

        """
        process_cpu_time = self.process_cpu_time()
        if process_cpu_time == 0:
            return 0
        total_cpu_time = self.total_cpu_time()
        if not self.prev_temp_data['cpu']:
            self.prev_temp_data['cpu'] = {'process_cpu_time': process_cpu_time, 'total_cpu_time': total_cpu_time,
                                          'time': self.collect_time}
            return None
        else:
            prev_cpu_time = self.prev_temp_data['cpu']
            dt_process_time = process_cpu_time - prev_cpu_time['process_cpu_time']
            dt_total_time = total_cpu_time - prev_cpu_time['total_cpu_time']
            cpu = 100 * ((dt_process_time * 1.0) / dt_total_time)
            if cpu < 0:
                LOGGING.error("cpu data error: %s" % (repr(prev_cpu_time) + "," + str(process_cpu_time) + "," + str(total_cpu_time)))
            self.prev_temp_data['cpu'] = {'process_cpu_time': process_cpu_time, 'total_cpu_time': total_cpu_time,
                                          'time': self.collect_time}
            return cpu

    def uid(self):
        if self._uid:
            return self._uid
        output = self.adb.shell("cat /proc/{pid}/status".format(pid=self._pid))
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
        Returns (当前流量 - 上一个时间点的流量) / (时间差) / 1024 = n KB/s
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
                    return round((ret - prev_net_flow['bytes'])*1.0 / ((self.collect_time - prev_net_flow['time']) * 1024), 2)
                else:
                    return ret - prev_net_flow['bytes']
        return None
