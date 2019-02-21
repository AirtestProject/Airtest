# Airtest &middot; [![Build status](https://travis-ci.org/AirtestProject/Airtest.svg?branch=master)](https://travis-ci.org/AirtestProject/Airtest)

**跨平台的UI自动化框架，适用于游戏和App**


![image](./demo.gif)


## 快速开始

*   **各种运行：**Airtest提供了跨平台的API，包括安装应用、模拟输入、断言等。 基于图像识别技术定位UI元素，你无需嵌入任何代码即可进行自动化。

*   **扩展性：**Airtest提供了命令行和python接口，可以很容易地在大规模设备集群上运行。自动生成的HTML报告，包含详细步骤和录屏，让你迅速定位失败点。

*   **AirtestIDE：** 是一个强大的GUI工具，可以帮助你录制和调试自动化脚本。 AirtestIDE支持了完整的自动化流程：``录制脚本->真机回放->生成报告``。

*   **Poco:** [Poco](https://github.com/AirtestProject/Poco) 框架可以直接访问UI控件，支持主流平台和游戏引擎。通过Python API操作UI控件，可以实现更强大的自动化控制。

[从官网开始上手吧](http://airtest.netease.com/)


#### [跨平台支持](./docs/wiki/platforms.md)

| | | | | | | |
|-|-|-|-|-|-|-|
Android|[iOS](https://github.com/AirtestProject/iOS-Tagent)|Windows|Unity|Cocos2dx|白鹭引擎|[微信小程序](http://airtest.netease.com/blog/tutorial/WechatSmallProgram/)|

## 安装

使用 `pip` 安装Airtest框架

```Shell
pip install -U airtest
```

在Mac/Linux系统下，需要手动赋予adb可执行权限

```Shell
# mac系统
cd {your_python_path}/site-packages/airtest/core/android/static/adb/mac
# linux系统
# cd {your_python_path}/site-packages/airtest/core/android/static/adb/linux
chmod +x adb
```

如果你需要使用GUI工具，请从 [官网](http://airtest.netease.com/) 下载AirtestIDE。


## 文档

完整的Airtest文档请看 [readthedocs](http://airtest.readthedocs.io/)。


## 例子

Airtest希望提供平台无关的API，让你的自动化代码可以运行在不同平台的应用上。

1. 使用 [connect_device](http://airtest.readthedocs.io/zh_CN/latest/README_MORE.html#connect-device) 来连接任意Android设备或者Windows窗口。
1. 使用 [模拟操作](http://airtest.readthedocs.io/zh_CN/latest/README_MORE.html#simulate-input) 的API来自动化你的游戏或者App。
1. **不要** 忘记 [声明断言](http://airtest.readthedocs.io/zh_CN/latest/README_MORE.html#make-assertion) 来验证结果。 


```Python
from airtest.core.api import *

# 通过ADB连接本地Android设备
init_device("Android")
# 或者使用connect_device函数
# connect_device("Android:///")
connect_device("Android:///")
install("path/to/your/apk")
start_app("package_name_of_your_apk")
touch(Template("image_of_a_button.png"))
swipe(Template("slide_start.png"), Template("slide_end.png"))
assert_exists(Template("success.png"))
keyevent("BACK")
home()
uninstall("package_name_of_your_apk")
```

更详细的说明请看 [Airtest Python API 文档](http://airtest.readthedocs.io/zh_CN/latest/all_module/airtest.core.api.html) 或者直接看 [API代码](./airtest/core/api.py) 。


## 用命令行运行 ``.air`` 脚本

使用AirtestIDE你可以非常轻松地录制一个自动化脚本并保存为 ``.air`` 目录结构。
Airtest命令行则让你能够脱离IDE，在不同宿主机器和被测设备上运行自动化脚本。

```Shell
# 在本地ADB连接的安卓手机上运行脚本
airtest run "path to your air dir" --device Android:///

# 在Windows应用上运行脚本
airtest run "path to your air dir" --device "Windows:///?title_re=Unity.*"

# 生成HTML报告
airtest report "path to your air dir"

# 也可以用python -m的方式使用命令行
python -m airtest run "path to your air dir" --device Android:///
```

试试样例[airtest/playground/test_blackjack.air](./playground/test_blackjack.air)，更多用法看[命令行用法](http://airtest.readthedocs.io/zh_CN/latest/README_MORE.html#running-air-from-cli)。


## 贡献代码

欢迎大家fork和提pull requests。[这里需要大家的帮助](./docs/wiki/platforms.md#pull-request-guide)


## 致谢

感谢以下仓库让Airtest变得更好：

- [stf](https://github.com/openstf)
- [atx](https://github.com/NetEaseGame/ATX)
- [pywinauto](https://github.com/pywinauto/pywinauto)

## 关于我们

访问我们的[官网](http://airtest.netease.com/)获得更多信息，同时欢迎大家扫描下方二维码关注我们的微信公众号：AirtestProject

![image](http://airtest.netease.com/static/img/social_media/wechat_qrcode.jpg)
