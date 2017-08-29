#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
import traceback
from collections import defaultdict


def gen_pfm_json(log_path):
    """
    检查log文件夹下是否有符合格式的性能数据log文件，如果有就生成对应的Json文件
    Parameters
    ----------
    log_path

    Returns
    -------

    """
    log_pattern = r"pfm_?(?P<serialno>\w*).txt"
    ret = []
    devices = []
    trace_list = []

    for f in os.listdir(log_path):
        f_match = re.match(log_pattern, f)
        if not f_match:
            continue
        serialno = f_match.groupdict()['serialno']
        devices.append(serialno)
        data, trace = trans_log_json(os.path.join(log_path, f))
        data["serialno"] = serialno
        ret.append(data)
        if trace:
            trace_list.extend(trace)
    if not ret:
        return [], [], ""
    content = "json_data=" + json.dumps(ret)
    output = os.path.join(log_path, "pfm_local.json")
    try:
        with open(output, "w+") as f:
            f.write(content)
        with open(os.path.join(log_path, "pfm.json"), "w+") as f:
            f.write(json.dumps(ret))
    except:
        print traceback.format_exc()
        return [], [], ""
    return devices, trace_list, log_path


def trans_log_json(log="pfm.txt"):
    """
    把运行中生成的log文件生成json格式，并且进行一定的处理
    Parameters
    ----------
    log

    Returns 解析出来的数据和traceback内容
    -------

    """
    data = defaultdict(lambda: defaultdict(lambda: 0))
    ret = {"cpu": [], "pss": [], "net_flow": [],
           "keys": ["cpu", "pss", "net_flow"],
           "title": log}
    times = []
    transback_content = []
    func_dict = {
        "cpu": cpu,
        "pss": pss,
        "net_flow": net_flow,
    }
    with open(log) as f:
        for item in f.readlines():
            item = json.loads(item)
            if item["name"] == "traceback":
                transback_content.append(item["value"])
                continue
            try:
                data[item["time"]][item["name"]] = func_dict[item["name"]](item["value"]) if item["name"] in func_dict else item["value"]
            except:
                data[item["time"]][item["name"]] = 0
            if item["time"] not in times:
                times.append(item["time"])

    for t in times:
        for k in func_dict.keys():
            ret[k].append(data[t][k])
    ret["times"] = times
    return ret, transback_content


def cpu(value):
    return round(float(value), 2)


def pss(value):
    """
    内存的单位是KB，转为MB
    Parameters
    ----------
    value pss kb

    Returns pss/1024
    -------

    """
    return round(float(value)/1024.0, 2)


def net_flow(value):
    """
    流量，输入值为 n B/s
    Parameters
    ----------
    value 当前流量值 B/S

    Returns 流量值KB/S
    -------

    """
    return round(float(value)/1024.0, 2)
