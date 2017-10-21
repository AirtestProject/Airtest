# coding=utf-8

"""本文件用于存放一些计算函数，比如图像适配、搜索区域预测."""


def no_resize(w_a, h_a, resolution_a, resolution_b):
    """无缩放策略."""
    return w_a, h_a


def cocos_min_strategy(w, h, sch_resolution, src_resolution, design_resolution=(960, 640)):
    """图像缩放规则: COCOS中的MIN策略."""
    # 输入参数: w-h待缩放图像的宽高，sch_resolution为待缩放图像的来源分辨率
    #           src_resolution 待适配屏幕的分辨率  design_resolution 软件的设计分辨率
    # 需要分别算出对设计分辨率的缩放比，进而算出src\sch有效缩放比。
    scale_sch = min(1.0 * sch_resolution[0] / design_resolution[0], 1.0 * sch_resolution[1] / design_resolution[1])
    scale_src = min(1.0 * src_resolution[0] / design_resolution[0], 1.0 * src_resolution[1] / design_resolution[1])
    scale = scale_src / scale_sch
    h_re, w_re = int(h * scale), int(w * scale)
    return w_re, h_re


def predict_area(im_source, op_pos, radius_x, radius_y, src_resolution=None):
    """根据参数进行screen的预测区域."""
    # 预测操作位置: (按照比例进行点预测) clk_x, clk_y是规划为比例的
    clk_x, clk_y = op_pos
    # 如果没有传递
    if src_resolution:
        res_x, res_y = src_resolution
    else:
        res_y, res_x = im_source.shape[:2]
    prePos_x, prePos_y = clk_x * res_x + 0.5 * res_x, clk_y * res_x + 0.5 * res_y

    def safe_xy(val, min_val, max_val):
        return min(max(min_val, val), max_val)

    # 再以预测点为中心，进行范围提取:
    start_x = int(safe_xy(prePos_x - radius_x, 0, res_x - 1))
    end_x = int(safe_xy(prePos_x + radius_x, 0, res_x - 1))
    start_y = int(safe_xy(prePos_y - radius_y, 0, res_y - 1))
    end_y = int(safe_xy(prePos_y + radius_y, 0, res_y - 1))

    # 如果发现预测区域完全在图像外，预测区域将只剩下一条像素，预测失败，直接raise:
    if start_x == end_x or start_y == end_y:
        img_src, left_top_pos = im_source, (0, 0)
        log_info = "Predict area's width or height has just one pixel, abandon prediction."
    else:
        # 预测区域正常，则截取预测区域，并将预测区域在源图像中的位置一并返回:
        img_src = im_source[start_y:end_y, start_x:end_x]
        left_top_pos = (start_x, start_y)
        # 输出调试信息.
        log_info = "predict rect:  X (%(start_x)s:%(end_x)s)   Y (%(start_y)s:%(end_y)s)" % {"start_x": start_x, "end_x":end_x, "start_y": start_y, "end_y": end_y}

    return img_src, left_top_pos, log_info
