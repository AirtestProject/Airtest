#!/usr/bin/env python
# -*- encoding=utf-8 -*-

"""Unittest for aircv."""


import unittest
from airtest.aircv import imread
from airtest.aircv.keypoint_matching import *  # noqa
from airtest.aircv.keypoint_matching_contrib import *  # noqa
from airtest.aircv.template_matching import *  # noqa
from airtest.aircv.sift import find_sift
from airtest.aircv.template import find_template, find_all_template


class TestAircv(unittest.TestCase):
    """Test aircv."""

    # 2960*1440设备 内存耗费： kaze (2GB) >> sift > akaze >> surf > brisk > brief > orb > tpl
    # 单纯效果,推荐程度： tpl > surf ≈ sift > kaze > brisk > akaze> brief > orb
    # 有限内存,推荐程度： tpl > surf > sift > brisk > akaze > brief > orb >kaze

    THRESHOLD = 0.7
    RGB = True

    @classmethod
    def setUpClass(cls):
        cls.keypoint_sch = imread("matching_images/keypoint_search.png")
        cls.keypoint_src = imread("matching_images/keypoint_screen.png")

        cls.template_sch = imread("matching_images/template_search.png")
        cls.template_src = imread("matching_images/template_screen.png")

    @classmethod
    def tearDownClass(cls):
        pass

    def test_find_template(self):
        """Template matching."""
        result = TemplateMatching(self.template_sch, self.template_src, threshold=self.THRESHOLD, rgb=self.RGB).find_best_result()
        self.assertIsInstance(result, dict)

    def test_find_all_template(self):
        """Template matching."""
        result = TemplateMatching(self.template_sch, self.template_src, threshold=self.THRESHOLD, rgb=self.RGB).find_all_results()
        self.assertIsInstance(result, list)

    def test_find_kaze(self):
        """KAZE matching."""
        # 较慢,稍微稳定一点.
        result = KAZEMatching(self.keypoint_sch, self.keypoint_src, threshold=self.THRESHOLD, rgb=self.RGB).find_best_result()
        self.assertIsInstance(result, dict)

    def test_find_brisk(self):
        """BRISK matching."""
        # 快,效果一般,不太稳定
        result = BRISKMatching(self.keypoint_sch, self.keypoint_src, threshold=self.THRESHOLD, rgb=self.RGB).find_best_result()
        self.assertIsInstance(result, dict)

    def test_find_akaze(self):
        """AKAZE matching."""
        # 较快,效果较差,很不稳定
        result = AKAZEMatching(self.keypoint_sch, self.keypoint_src, threshold=self.THRESHOLD, rgb=self.RGB).find_best_result()
        self.assertIsInstance(result, dict)

    def test_find_orb(self):
        """ORB matching."""
        # 很快,效果垃圾
        result = ORBMatching(self.keypoint_sch, self.keypoint_src, threshold=self.THRESHOLD, rgb=self.RGB).find_best_result()
        self.assertIsInstance(result, dict)

    def test_contrib_find_sift(self):
        """SIFT matching (----need OpenCV contrib module----)."""
        # 慢,最稳定
        result = SIFTMatching(self.keypoint_sch, self.keypoint_src, threshold=self.THRESHOLD, rgb=self.RGB).find_best_result()
        self.assertIsInstance(result, dict)

    def test_contrib_find_surf(self):
        """SURF matching (----need OpenCV contrib module----)."""
        # 快,效果不错
        result = SURFMatching(self.keypoint_sch, self.keypoint_src, threshold=self.THRESHOLD, rgb=self.RGB).find_best_result()
        self.assertIsInstance(result, dict)

    def test_contrib_find_brief(self):
        """BRIEF matching (----need OpenCV contrib module----)."""
        # 识别特征点少,只适合强特征图像的匹配
        result = BRIEFMatching(self.keypoint_sch, self.keypoint_src, threshold=self.THRESHOLD, rgb=self.RGB).find_best_result()
        self.assertIsInstance(result, dict)

    def test_contrib_func_find_sift(self):
        """Test find_sift function in sift.py."""
        result = find_sift(self.keypoint_src, self.keypoint_sch, threshold=self.THRESHOLD, rgb=self.RGB)
        self.assertIsInstance(result, dict)

    def test_func_find_template(self):
        """Test find_template function in template.py."""
        result = find_template(self.template_src, self.template_sch, threshold=self.THRESHOLD, rgb=self.RGB)
        self.assertIsInstance(result, dict)

    def test_func_find_all_template(self):
        """Test find_all_template function in template.py."""
        result = find_all_template(self.template_src, self.template_sch, threshold=self.THRESHOLD, rgb=self.RGB)
        self.assertIsInstance(result, list)


if __name__ == '__main__':
    unittest.main()
