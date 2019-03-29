# -*- coding: utf-8 -*-

"""This module test the Airtest keypoint matching methods."""

from random import random
import matplotlib.pyplot as plt

from plot import PlotResult
from profile_recorder import ProfileRecorder


def profile_different_methods(search_file, screen_file, method_list, dir_path, file_name):
    """对指定的图片进行性能测试."""
    profiler = ProfileRecorder(0.05)
    # 加载图片
    profiler.load_images(search_file, screen_file)
    # 传入待测试的方法列表
    profiler.profile_methods(method_list)
    # 将性能数据写入文件
    profiler.wite_to_json(dir_path, file_name)


def plot_one_image_result(dir_path, file_name):
    """绘制结果."""
    plot_object = PlotResult(dir_path, file_name)
    plot_object.plot_cpu_mem_keypoints()


def test_and_profile_and_plot(search_file, screen_file, dir_path, file_name, method_list):
    """单张图片：性能测试+绘制结果."""
    # 写入性能数据
    profile_different_methods(search_file, screen_file, method_list, dir_path, file_name)
    # 绘制图形
    plot_one_image_result(dir_path, file_name)


def test_and_profile_all_images(method_list):
    """测试各种images，作对比."""
    # 生成性能数据1
    search_file, screen_file = "sample\\high_dpi\\tpl1551940579340.png", "sample\\high_dpi\\tpl1551944272194.png"
    high_dpi_dir_path, high_dpi_file_name = "result", "high_dpi.json"
    profile_different_methods(search_file, screen_file, method_list, high_dpi_dir_path, high_dpi_file_name)
    # 生成性能数据2
    search_file, screen_file = "sample\\rich_texture\\search.png", "sample\\rich_texture\\screen.png"
    rich_texture_dir_path, rich_texture_file_name = "result", "rich_texture.json"
    profile_different_methods(search_file, screen_file, method_list, rich_texture_dir_path, rich_texture_file_name)
    # 生成性能数据3
    search_file, screen_file = "sample\\text\\search.png", "sample\\text\\screen.png"
    text_dir_path, text_file_name = "result", "text.json"
    profile_different_methods(search_file, screen_file, method_list, text_dir_path, text_file_name)


def plot_profiled_all_images_table(method_list):
    """绘制多个图片的结果."""
    high_dpi_dir_path, high_dpi_file_name = "result", "high_dpi.json"
    rich_texture_dir_path, rich_texture_file_name = "result", "rich_texture.json"
    text_dir_path, text_file_name = "result", "text.json"

    image_list = ['high_dpi', 'rich_texture', 'text']
    # high_dpi_method_exec_info
    high_dpi_plot_object = PlotResult(high_dpi_dir_path, high_dpi_file_name)
    high_dpi_method_exec_info = high_dpi_plot_object.method_exec_info
    # rich_texture_method_exec_info
    rich_texture_plot_object = PlotResult(rich_texture_dir_path, rich_texture_file_name)
    rich_texture_method_exec_info = rich_texture_plot_object.method_exec_info
    # text_method_exec_info
    text_plot_object = PlotResult(text_dir_path, text_file_name)
    text_method_exec_info = text_plot_object.method_exec_info

    exec_info_list = [high_dpi_method_exec_info, rich_texture_method_exec_info, text_method_exec_info]
    # 提取对应结果:
    mem_compare_dict, cpu_compare_dict, succeed_compare_dict = {}, {}, {}
    for index, method in enumerate(method_list):
        mem_list, cpu_list, succeed_list = [], [], []
        for exec_info in exec_info_list:
            current_method_exec_info = exec_info[index]
            mem_list.append(round(current_method_exec_info["mem_max"], 2))  # MB
            # mem_list.append(round(current_method_exec_info["mem_max"] / 1024, 2))  # GB
            cpu_list.append(round(current_method_exec_info["cpu_max"], 2))
            succeed_ret = True if current_method_exec_info["result"] else False
            succeed_list.append(succeed_ret)

        mem_compare_dict.update({method: mem_list})
        cpu_compare_dict.update({method: cpu_list})
        succeed_compare_dict.update({method: succeed_list})

    color_list = get_color_list(method_list)

    # # 绘制三张表格
    # plot_compare_table(image_list, method_list, color_list, mem_compare_dict, "memory (GB)", 311)
    # plot_compare_table(image_list, method_list, color_list, cpu_compare_dict, "CPU (%)", 312)
    # plot_compare_table(image_list, method_list, color_list, succeed_compare_dict, "Result", 313)
    # plt.show()

    # 绘制两个曲线图、一个表格图：
    plot_compare_curves(image_list, method_list, color_list, mem_compare_dict, "Title: Memory (GB)", 311)
    plot_compare_curves(image_list, method_list, color_list, cpu_compare_dict, "Title: CPU (%)", 312)
    plot_compare_table(image_list, method_list, color_list, succeed_compare_dict, "Title: Result", 313)
    plt.show()


def get_color_list(method_list):
    """获取method对应的color列表."""
    color_list = []
    for method in method_list:
        color = tuple([random() for _ in range(3)])  # 随机颜色画线
        color_list.append(color)
    return color_list


def plot_compare_table(image_list, method_list, color_list, compare_dict, fig_name="", fig_num=111):
    """绘制了对比表格."""
    row_labels = image_list
    # 写入值：
    table_vals = []
    for i in range(len(row_labels)):
        row_vals = []
        for method in method_list:
            row_vals.append(compare_dict[method][i])
        table_vals.append(row_vals)
    # 绘制表格图
    colors = [[(0.95, 0.95, 0.95) for c in range(len(method_list))] for r in range(len(row_labels))]  # cell的颜色
    # plt.figure(figsize=(8, 4), dpi=120)
    plt.subplot(fig_num)
    plt.title(fig_name)  # 绘制标题
    lightgrn = (0.5, 0.8, 0.5)  # 这个是label的背景色
    plt.table(cellText=table_vals,
              rowLabels=row_labels,
              colLabels=method_list,
              rowColours=[lightgrn] * len(row_labels),
              colColours=color_list,
              cellColours=colors,
              cellLoc='center',
              loc='upper left')

    plt.axis('off')  # 关闭坐标轴


def plot_compare_curves(image_list, method_list, color_list, compare_dict, fig_name="", fig_num=111):
    """绘制对比曲线."""
    plt.subplot(fig_num)
    plt.title(fig_name, loc="center")  # 设置绘图的标题
    mix_ins = []
    for index, method in enumerate(method_list):
        mem_ins = plt.plot(image_list, compare_dict[method], "-", label=method, color=color_list[index], linestyle='-', marker='.')
        # mem_ins = plt.plot(image_list, compare_dict[method], "-", label=method, color='deepskyblue', linestyle='-', marker='.')
        mix_ins.append(mem_ins)

    plt.legend(loc='upper right')  # 说明标签的位置
    plt.grid()  # 加网格
    # plt.xlabel("Image")
    plt.ylabel("Mem(MB)")
    plt.ylim(bottom=0)


if __name__ == '__main__':
    method_list = ["kaze", "brisk", "akaze", "orb", "sift", "surf", "brief"]

    # 针对一张图片，绘制该张图片的cpu和mem使用情况.截屏[2907, 1403] 截图[1079, 804]
    search_file, screen_file = "sample\\high_dpi\\tpl1551940579340.png", "sample\\high_dpi\\tpl1551944272194.png"
    dir_path, file_name = "result", "high_dpi.json"
    test_and_profile_and_plot(search_file, screen_file, dir_path, file_name, method_list)

    # 测试多张图片，写入性能测试数据
    test_and_profile_all_images(method_list)
    # 对比绘制多张图片的结果
    plot_profiled_all_images_table(method_list)
