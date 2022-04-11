#!/usr/bin/env python
# -*- encoding=utf-8 -*-

"""Unittest for aircv."""


import unittest
from airtest.aircv import imread
from airtest.aircv import SIFT, SURF, ORB, AKAZE, MatchTemplate


class TestAircv(unittest.TestCase):
    """Test aircv."""

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
        match = MatchTemplate()
        result = match.find_best_result(im_source=self.template_src, im_search=self.template_sch, threshold=self.THRESHOLD, rgb=self.RGB)
        self.assertIsInstance(result, dict)

    def test_find_all_template(self):
        """Template matching."""
        match = MatchTemplate()
        result = match.find_all_results(im_source=self.template_src, im_search=self.template_sch, threshold=self.THRESHOLD, rgb=self.RGB)
        self.assertIsInstance(result, list)

    def test_find_akaze(self):
        """AKAZE matching."""
        match = AKAZE()
        result = match.find_best_result(im_source=self.template_src, im_search=self.template_sch, threshold=self.THRESHOLD, rgb=self.RGB)
        self.assertIsInstance(result, dict)

    def test_find_orb(self):
        """ORB matching."""
        match = ORB()
        result = match.find_best_result(im_source=self.template_src, im_search=self.template_sch, threshold=self.THRESHOLD, rgb=self.RGB)
        self.assertIsInstance(result, dict)

    def test_contrib_find_sift(self):
        """SIFT matching (----need OpenCV contrib module----)."""
        # 慢,最稳定
        match = SIFT()
        result = match.find_best_result(im_source=self.template_src, im_search=self.template_sch, threshold=self.THRESHOLD, rgb=self.RGB)
        self.assertIsInstance(result, dict)

    def test_contrib_find_surf(self):
        """SURF matching (----need OpenCV contrib module----)."""
        match = SURF()
        result = match.find_best_result(im_source=self.template_src, im_search=self.template_sch, threshold=self.THRESHOLD, rgb=self.RGB)
        self.assertIsInstance(result, dict)



if __name__ == '__main__':
    unittest.main()
