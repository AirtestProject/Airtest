# -*- coding: utf-8 -*-

"""This module test the Airtest keypoint matching methods."""

import os
import cv2
import json
import time
import psutil
import threading
import numpy as np
from copy import deepcopy
from random import random

from airtest.aircv import imread, mark_point
from airtest.aircv.keypoint_matching import KAZEMatching, BRISKMatching, AKAZEMatching, ORBMatching
from airtest.aircv.keypoint_matching_contrib import SIFTMatching, SURFMatching, BRIEFMatching


class CheckKeypointResult(object):
    """查看基于特征点的图像结果."""

    RGB = False
    THRESHOLD = 0.7
    MATCHING_METHODS = {
        "kaze": KAZEMatching,
        "brisk": BRISKMatching,
        "akaze": AKAZEMatching,
        "orb": ORBMatching,
        "sift": SIFTMatching,
        "surf": SURFMatching,
        "brief": BRIEFMatching,
    }

    def __init__(self, im_search, im_source, threshold=0.8, rgb=True):
        super(CheckKeypointResult, self).__init__()
        self.im_source = im_source
        self.im_search = im_search
        self.threshold = threshold or self.THRESHOLD
        self.rgb = rgb or self.RGB
        # 初始化方法对象
        self.refresh_method_objects()

    def refresh_method_objects(self):
        """初始化方法对象."""
        self.method_object_dict = {}
        for key, method in self.MATCHING_METHODS.items():
            method_object = method(self.im_search, self.im_source, self.threshold, self.rgb)
            self.method_object_dict.update({key: method_object})

    def _get_result(self, method_name="kaze"):
        """获取特征点."""
        method_object = self.method_object_dict.get(method_name)
        # 提取结果和特征点:
        try:
            result = method_object.find_best_result()
        except Exception:
            import traceback
            traceback.print_exc()
            return [], [], [], None

        return method_object.kp_sch, method_object.kp_src, method_object.good, result

    def get_and_plot_keypoints(self, method_name, plot=False):
        """获取并且绘制出特征点匹配结果."""
        if method_name not in self.method_object_dict.keys():
            print("'%s' is not in MATCHING_METHODS" % method_name)
            return None
        kp_sch, kp_src, good, result = self._get_result(method_name)

        if not plot or result is None:
            return kp_sch, kp_src, good, result
        else:
            im_search, im_source = deepcopy(self.im_search), deepcopy(self.im_source)
            # 绘制特征点识别情况、基于特征的图像匹配结果:
            h_sch, w_sch = im_search.shape[:2]
            h_src, w_src = im_source.shape[:2]
            # init the plot image:
            plot_img = np.zeros([max(h_sch, h_src), w_sch + w_src, 3], np.uint8)
            plot_img[:h_sch, :w_sch, :] = im_search
            plot_img[:h_src, w_sch:, :] = im_source
            # plot good matche points:
            for m in good:
                color = tuple([int(random() * 255) for _ in range(3)])  # 随机颜色画线
                cv2.line(plot_img, (int(kp_sch[m.queryIdx].pt[0]), int(kp_sch[m.queryIdx].pt[1])), (int(kp_src[m.trainIdx].pt[0] + w_sch), int(kp_src[m.trainIdx].pt[1])), color)
            # plot search_image
            for kp in kp_sch:
                color = tuple([int(random() * 255) for _ in range(3)])  # 随机颜色画点
                pos = (int(kp.pt[0]), int(kp.pt[1]))
                mark_point(im_search, pos, circle=False, color=color, radius=5)
            # plot source_image
            for kp in kp_src:
                color = tuple([int(random() * 255) for _ in range(3)])  # 随机颜色画点
                pos = (int(kp.pt[0]), int(kp.pt[1]))
                mark_point(im_source, pos, circle=False, color=color, radius=10)

            from airtest.aircv import show
            show(plot_img)
            show(im_search)
            show(im_source)


class RecordThread(threading.Thread):
    """记录CPU和内存数据的thread."""

    def __init__(self, interval=0.1):
        super(RecordThread, self).__init__()
        self.pid = os.getpid()
        self.interval = interval

        self.cpu_num = psutil.cpu_count()
        self.process = psutil.Process(self.pid)

        self.profile_data = []
        self.stop_flag = False

    def set_interval(self, interval):
        """设置数据采集间隔."""
        self.interval = interval

    def run(self):
        """开始线程."""
        while not self.stop_flag:
            timestamp = time.time()
            cpu_percent = self.process.cpu_percent() / self.cpu_num
            # mem_percent = mem = self.process.memory_percent()
            mem_info = dict(self.process.memory_info()._asdict())
            mem_gb_num = mem_info.get('rss', 0) / 1024 / 1024
            # 记录类变量
            self.profile_data.append({"mem_gb_num": mem_gb_num, "cpu_percent": cpu_percent, "timestamp": timestamp})
            # 记录cpu和mem_gb_num
            time.sleep(self.interval)
            # print("--> mem_gb_num:", mem_gb_num)


class ProfileRecorder(object):
    """帮助用户记录性能数据."""

    def __init__(self, profile_interval=0.1):
        super(ProfileRecorder, self).__init__()

        self.record_thread = RecordThread()
        self.record_thread.set_interval(profile_interval)

    def load_images(self, search_file, source_file):
        """加载待匹配图片."""
        self.search_file, self.source_file = search_file, source_file
        self.im_search, self.im_source = imread(self.search_file), imread(self.source_file)
        # 初始化对象
        self.check_macthing_object = CheckKeypointResult(self.im_search, self.im_source)

    def profile_methods(self, method_list):
        """帮助函数执行时记录数据."""
        self.method_exec_info = []
        # 开始数据记录进程
        self.record_thread.stop_flag = False
        self.record_thread.start()

        for name in method_list:
            if name not in self.check_macthing_object.MATCHING_METHODS.keys():
                continue
            time.sleep(3)  # 留出绘图空白区
            start_time = time.time()  # 记录开始时间
            print("--->>> start '%s' matching:\n" % name)
            kp_sch, kp_src, good, result = self.check_macthing_object.get_and_plot_keypoints(name)  # 根据方法名绘制对应的识别结果
            print("\n\n\n")
            end_time = time.time()  # 记录结束时间
            time.sleep(3)  # 留出绘图空白区
            # 记录本次匹配的相关数据
            ret_info = {
                "name": name,
                "start_time": start_time,
                "end_time": end_time,
                "result": result,
                "kp_sch": len(kp_sch),
                "kp_src": len(kp_src),
                "good": len(good)}
            self.method_exec_info.append(ret_info)

        self.record_thread.stop_flag = True

    def wite_to_json(self, dir_path="", file_name=""):
        """将性能数据写入文件."""
        # 提取数据
        data = {
            "plot_data": self.record_thread.profile_data,
            "method_exec_info": self.method_exec_info,
            "search_file": self.search_file,
            "source_file": self.source_file}
        # 写入文件
        file_path = os.path.join(dir_path, file_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        json.dump(data, open(file_path, "w+"), indent=4)


def main():
    # 截屏[2907, 1403] 截图[1079, 804]
    search_file = "sample\\high_dpi\\tpl1551940579340.png"
    screen_file = "sample\\high_dpi\\tpl1551944272194.png"
    # 准备性能数据记录
    profiler = ProfileRecorder(0.05)
    profiler.load_images(search_file, screen_file)
    profiler.profile_methods(["kaze", "brisk", "akaze", "orb", "sift", "surf", "brief"])
    profiler.wite_to_json(dir_path="result", file_name="high_dpi.json")


if __name__ == '__main__':
    main()
