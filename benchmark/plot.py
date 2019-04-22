# -*- coding: utf-8 -*-

"""This module test the Airtest keypoint matching methods."""

import os
import anyconfig
import numpy as np
from copy import deepcopy
from matplotlib import rc
from datetime import datetime
import matplotlib.pyplot as plt


class PlotResult(object):
    """绘制单张图片的方法对比结果."""

    def __init__(self, dir_path="", file_name=""):
        super(PlotResult, self).__init__()

        # 提取数据:
        if file_name:
            file_path = os.path.join(dir_path, file_name)
            self.data = self.load_file(file_path)
            self.extract_data()
        else:
            raise Exception("Profile result file not exists..")

    def load_file(self, file, print_info=True):
        if print_info:
            print("loading config from :", repr(file))
        try:
            config = anyconfig.load(file, ignore_missing=True)
            return config
        except ValueError:
            print("loading config failed...")
            return {}

    def extract_data(self):
        """从数据中获取到绘图相关的有用信息."""
        self.time_axis = []
        self.cpu_axis = []
        self.mem_axis = []
        self.timestamp_list = []
        plot_data = self.data.get("plot_data", [])
        # 按照时间分割线，划分成几段数据，取其中的最值
        for i in plot_data:
            timestamp = i["timestamp"]
            self.timestamp_list.append(timestamp)
            timestamp = round(timestamp, 1)
            cpu_percent = i["cpu_percent"]
            mem_gb_num = i["mem_gb_num"]
            date = datetime.fromtimestamp(timestamp)
            # 添加坐标轴
            self.time_axis.append(date)
            self.cpu_axis.append(cpu_percent)
            self.mem_axis.append(mem_gb_num)

        # 获取各种方法执行过程中的cpu和内存极值:
        self.get_each_method_maximun_cpu_mem()

    def get_each_method_maximun_cpu_mem(self):
        """获取每个方法中的cpu和内存耗费最值点."""
        # 本函数用于丰富self.method_exec_info的信息:存入cpu、mem最值点
        self.method_exec_info = deepcopy(self.data.get("method_exec_info", []))
        method_exec_info = deepcopy(self.method_exec_info)  # 用来辅助循环
        method_index, cpu_max, cpu_max_time, mem_max, mem_max_time = 0, 0, 0, 0, 0  # 临时变量
        self.max_mem = 0
        for index, timestamp in enumerate(self.timestamp_list):
            # method_exec_info是按顺序的,逐个遍历找出每个method_exec_info中的cpu和mem的最值点和timestamp:
            start, end = method_exec_info[0]["start_time"], method_exec_info[0]["end_time"]
            if timestamp < start:
                # 方法正式start之前的数据，不能参与方法内的cpu、mem计算，直接忽略此条数据
                continue
            elif timestamp <= end:
                # 方法执行期间的数据,纳入最值比较:
                if self.cpu_axis[index] > cpu_max:
                    cpu_max, cpu_max_time = self.cpu_axis[index], timestamp
                if self.mem_axis[index] > mem_max:
                    mem_max, mem_max_time = self.mem_axis[index], timestamp
                continue
            else:
                # 本次方法筛选完毕，保存本方法的最值cpu和mem
                if cpu_max_time != 0 and mem_max_time != 0:
                    self.method_exec_info[method_index].update({"cpu_max": cpu_max, "mem_max": mem_max, "cpu_max_time": cpu_max_time, "mem_max_time": mem_max_time})
                # 保存最大的内存，后面绘图时用
                if mem_max > self.max_mem:
                    self.max_mem = mem_max
                cpu_max, mem_max = 0, 0  # 临时变量
                # 准备进行下一个方法的检查，发现已经检查完则正式结束
                del method_exec_info[0]
                if method_exec_info:
                    method_index += 1  # 进行下一个方法时:当前方法的序号+1
                    continue
                else:
                    break

    def _get_graph_title(self):
        """获取图像的title."""
        start_time = datetime.fromtimestamp(int(self.timestamp_list[0]))
        end_time = datetime.fromtimestamp(int(self.timestamp_list[-1]))
        end_time = end_time.strftime('%H:%M:%S')
        title = "Timespan: %s —— %s" % (start_time, end_time)

        return title

    def plot_cpu_mem_keypoints(self):
        """绘制CPU/Mem/特征点数量."""
        plt.figure(1)
        # 开始绘制子图:
        plt.subplot(311)
        title = self._get_graph_title()
        plt.title(title, loc="center")  # 设置绘图的标题
        mem_ins = plt.plot(self.time_axis, self.mem_axis, "-", label="Mem(MB)", color='deepskyblue', linestyle='-', marker=',')
        # 设置数字标签
        plt.legend(mem_ins, ["Mem(MB)"], loc='upper right')  # 说明标签的位置
        plt.grid()  # 加网格
        plt.ylabel("Mem(MB)")
        plt.ylim(bottom=0)
        for method_exec in self.method_exec_info:
            start_date = datetime.fromtimestamp(method_exec["start_time"])
            end_date = datetime.fromtimestamp(method_exec["end_time"])
            plt.vlines(start_date, 0, self.max_mem, colors="c", linestyles="dashed")  # vlines(x, ymin, ymax)
            plt.vlines(end_date, 0, self.max_mem, colors="c", linestyles="dashed")  # vlines(x, ymin, ymax)
            # 绘制mem文字:
            x = datetime.fromtimestamp(method_exec["mem_max_time"])
            text = "%s: %d MB" % (method_exec["name"], method_exec["mem_max"])
            plt.text(x, method_exec["mem_max"], text, ha="center", va="bottom", fontsize=10)
            plt.plot(x, method_exec["mem_max"], 'bo', label="point")  # 绘制点

        # 绘制子图2
        plt.subplot(312)
        cpu_ins = plt.plot(self.time_axis, self.cpu_axis, "-", label="CPU(%)", color='red', linestyle='-', marker=',')
        plt.legend(cpu_ins, ["CPU(%)"], loc='upper right')  # 说明标签的位置
        plt.grid()  # 加网格
        plt.xlabel("Time(s)")
        plt.ylabel("CPU(%)")
        plt.ylim(0, 120)
        for method_exec in self.method_exec_info:
            start_date = datetime.fromtimestamp(method_exec["start_time"])
            end_date = datetime.fromtimestamp(method_exec["end_time"])
            plt.vlines(start_date, 0, 100, colors="c", linestyles="dashed")  # vlines(x, ymin, ymax)
            plt.vlines(end_date, 0, 100, colors="c", linestyles="dashed")  # vlines(x, ymin, ymax)
            # 绘制mem文字:
            x = datetime.fromtimestamp(method_exec["cpu_max_time"])
            text = "%s: %d%%" % (method_exec["name"], method_exec["cpu_max"])
            plt.text(x, method_exec["cpu_max"], text, ha="center", va="bottom", fontsize=10)
            plt.plot(x, method_exec["cpu_max"], 'ro', label="point")  # 绘制点

        # 绘制子图3
        plt.subplot(313)  # 绘制一下柱状图(关键点)
        # 设置轴向标签
        plt.xlabel('methods')
        plt.ylabel('keypoints number')
        method_list, method_pts_length_list, color_list = [], [], []
        for method_exec in self.method_exec_info:
            for item in ["kp_sch", "kp_src", "good"]:
                method_list.append("%s-%s" % (method_exec["name"], item))
                method_pts_length_list.append(method_exec[item])
                if method_exec["result"]:
                    color_list.append(["palegreen", "limegreen", "deepskyblue"][["kp_sch", "kp_src", "good"].index(item)])
                else:
                    color_list.append("tomato")
        method_x = np.arange(len(method_list)) + 1
        plt.bar(method_x, method_pts_length_list, width=0.35, align='center', color=color_list, alpha=0.8)
        plt.xticks(method_x, method_list, size='small', rotation=30)
        # 设置数字标签
        for x, y in zip(method_x, method_pts_length_list):
            plt.text(x, y + 10, "%d" % y, ha="center", va="bottom", fontsize=7)
        plt.ylim(0, max(method_pts_length_list) * 1.2)

        # 显示图像
        plt.show()


def main():
    # 绘制结果图
    plot_object = PlotResult(dir_path="result", file_name="high_dpi.json")
    plot_object.plot_cpu_mem_keypoints()


if __name__ == '__main__':
    main()
