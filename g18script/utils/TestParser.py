# -*- coding: utf-8 -*-
import os
import sys

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, '../../')
sys.path.append(PROJECT_DIR)
sys.path.insert(0, "..")

from moa import moa

import base


class TestParser(object):
    def __init__(self, testcase_file):
        self.tc = base.read_json_conf(testcase_file)
        self.scenes = self.tc['scenes']
        self.testcase = self.tc['testcase']
        self.log = base.setup_custom_logger(__name__)
        self.app = moa
        self.app.set_serialno()
        self.app.OP_DELAY = 0.5

    def run_click(self, params, img_dir):
        for param in params:
            param_array = param.split()
            # 一个参数：默认点击
            if len(param_array) == 1:
                click_img = self.safe_join_path(img_dir, param_array[0])
                self.app.touch(click_img)
            # 两个参数：点击后需判断
            if len(param_array) == 2:
                click_img = self.safe_join_path(img_dir, param_array[0])
                wait_img = self.safe_join_path(img_dir, param_array[1])
                self.app.touch(click_img)
                if not self.app.wait(wait_img):
                    self.log.error(u"期望图片：{}不存在".format(wait_img))
            # 三个参数：点击后判断，并自定义timeout
            if len(param_array) == 3:
                click_img = self.safe_join_path(img_dir, param_array[0])
                wait_img = self.safe_join_path(img_dir, param_array[1])
                self.app.touch(click_img)
                if not self.app.wait(wait_img, timeout=param_array[2]):
                    self.log.error(u"期望图片：{}不存在".format(wait_img))

    def run_action(self, actions, img_dir):
        for action in actions:
            if action["type"] == "click":
                self.run_click(action["params"], img_dir)

    @staticmethod
    def safe_get_value(dict_data, key):
        return dict_data[key] if key in dict_data.keys() else None

    @staticmethod
    def safe_join_path(parent_path, child_path):
        ret_path = os.path.join(parent_path, child_path) if parent_path else child_path
        return os.path.join(SCRIPT_DIR+"/../", ret_path.encode('utf-8'))

    def goto_scene(self, scene):
        if scene not in self.scenes.keys():
            self.log.error(u"场景:{} 未定义".format(scene))
        self.log.debug(u"前往:{}界面...".format(self.scenes[scene]["describe"]))
        from_scene = self.scenes[scene]["from"]
        # 递归前往目标场景
        if from_scene:
            self.goto_scene(from_scene)
        # 根据指定action前往目标场景
        img_dir = self.safe_get_value(self.scenes[scene], "img_dir")
        self.run_action(self.scenes[scene]["action"], img_dir)
        # 判断目标场景是否到达
        for feature_img in self.scenes[scene]["feature"]:
            wait_img = self.safe_join_path(img_dir, feature_img)
            if not self.app.wait(wait_img):
                self.log.error(u"前往:{}界面失败".format(self.scenes[scene]["describe"]))
                return False
        self.log.debug(u"前往:{}界面成功".format(self.scenes[scene]["describe"]))
        return True

    def run_case(self):
        self.log.debug(u"开始执行测试用例：{}...".format(self.testcase["describe"]))
        # 前往目标场景
        base_scene = self.testcase["base_scene"]
        if base_scene:
            self.goto_scene(base_scene)
        # 执行测试用例具体步骤
        for step in self.testcase["test_steps"]:
            self.log.debug(u"开始执行步骤：{}".format(step["name"]))
            img_dir = self.safe_get_value(self.testcase, "img_dir")
            self.run_action(step["action"], img_dir)


if __name__ == '__main__':
    tc = base.read_json_conf(os.path.join(PROJECT_DIR, 'g18/weekrun_files/shangcheng/testcase.json'))

    # tp = TestParser(os.path.join(PROJECT_DIR, 'g18/weekrun_files/shangcheng/testcase.json'))
