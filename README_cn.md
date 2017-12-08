Airtest
================

Airtest 自动化测试框架

## 快速开始

Airtest是一个专注于游戏自动化测试的UI测试框架，也可以用于各种源生App。支持Windows和Android平台，iOS支持正在开发中。

Airtest基于图像识别技术，并提供了跨平台的API，包括安装应用、模拟输入、断言等。测试脚本运行后可以自动生成详细的HTML测试报告。

**AirtestIDE**是一个开箱即用的GUI工具，可以帮助录制和调试测试脚本。AirtestIDE给QA人员提供了完整的工作流程支持：录制脚本->真机回放->生成报告


## 安装


**环境要求**

* 操作系统: 
  * Windows
  * MacOS X
  * Linux

* Python2.7 & Python3.3+

**安装Airtest**

Airtest可以直接从Git仓库安装。推荐使用``pip``来管理安装包和自动安装所有依赖。

```Shell
git clone https://github.com/Meteorix/airtest.git
pip install -e airtest

# 网易内部仓库
# git clone ssh://git@git-qa.gz.netease.com:32200/gzliuxin/airtest.git
```

因为Airtest还在快速开发中，这里使用`-e`来安装源码。以后你就可以直接使用`git pull`更新代码目录来升级Airtest了。

**尝试样例**

代码仓库内`playground`目录下提供了一些例子，现在你可以试试。


## 文档

浏览器打开[docs-release/index.html](./docs-release). 项目发布后，文档会放在readthedocs上。


## 使用方法

Airtest提供了简洁而且平台无关的API。这部分介绍了如何使用这些API来编写一个测试脚本，测试步骤如下：

1. 通过ADB连接一台安卓手机
1. 安装应用APK
1. 运行应用并截图
1. 模拟用户输入（点击、滑动、按键）
1. 卸载应用

```Python
from airtest.core.api import *

# connect to local device with adb
connect_device("Android:///")

# start your script here
install("path/to/your/apk")
start_app("package_name_of_your_apk")
snapshot("my_screenshot.png")
touch((100, 100))
touch("image_of_a_button.png")
swipe((100, 100), (200, 200))
swipe("button1.png", "button2.png")
keyevent("BACK")
home()
uninstall("package_name_of_your_apk")
```

更多API和使用方法，请参考完整的[API文档](./all_module/airtest.core.api.html)，或者直接看看[API代码](./airtest/core/api.py)


## 命令行使用

Airtest也提供了丰富的命令行功能，包括在不同设备上运行测试脚本，生成测试报告，获取脚本信息。 通过GUI工具**Airtest IDE**，你可以很快录制一个测试脚本。一个测试脚本通常是一个`.owl`结尾的文件目录，包含测试代码和模版图片。

使用AirtestIDE录制的测试脚本，可以直接通过Airtest的命令行来运行。你可以在命令行参数中指定连接的被测设备，这样就可以运行在不同的手机平台和宿主机器上。只要你的测试代码本身是平台无关的，你就可以在一个平台上录制脚本，然后在不同平台上运行。

下面的例子介绍了命令行的基本用法。可以配合我们提供的示例```airtest/playground/test_blackjack.owl/```来学习使用：


### 运行测试
````Shell
# 在不同设备上运行测试脚本
> python -m airtest run <path to your owl dir> --device Android:///
> python -m airtest run <path to your owl dir> --device Android://adbhost:adbport/serialno
> python -m airtest run <path to your owl dir> --device Windows:///
> python -m airtest run <path to your owl dir> --device iOS:///
...
# 显示帮助信息
> python -m airtest run -h
usage: __main__.py run [-h] [--device [DEVICE]] [--log [LOG]]
                       [--kwargs KWARGS] [--pre PRE] [--post POST]
                       script

positional arguments:
  script             owl path

optional arguments:
  -h, --help         show this help message and exit
  --device [DEVICE]  connect dev by uri string, e.g. Android:///
  --log [LOG]        set log dir, default to be script dir
  --kwargs KWARGS    extra kwargs used in script as global variables, e.g.
                     a=1,b=2
  --pre PRE          owl run before script, setup environment
  --post POST        owl run after script, clean up environment, will run
                     whether script success or fail
````


### 生成报告
```Shell
> python -m airtest report <path to your owl directory>
log.html
> python -m airtest report -h
usage: __main__.py report [-h] [--outfile OUTFILE] [--static_root STATIC_ROOT]
                          [--log_root LOG_ROOT] [--gif [GIF]]
                          [--gif_size [GIF_SIZE]] [--snapshot [SNAPSHOT]]
                          [--record RECORD [RECORD ...]]
                          [--new_report [NEW_REPORT]]
                          script

positional arguments:
  script                script filepath

optional arguments:
  -h, --help            show this help message and exit
  --outfile OUTFILE     output html filepath, default to be log.html
  --static_root STATIC_ROOT
                        static files root dir
  --log_root LOG_ROOT   log & screen data root dir, logfile should be
                        log_root/log.txt
  --gif [GIF]           generate gif, default to be log.gif
  --gif_size [GIF_SIZE]
                        gif thumbnails size (0.1-1), default 0.3
  --snapshot [SNAPSHOT]
                        get all snapshot
  --record RECORD [RECORD ...]
                        add screen record to log.html
  --new_report [NEW_REPORT]

```


### 获取脚本信息
```Shell
# 获取测试脚本的信息，以json格式输出，包括：作者、用例名、用例描述
> python -m airtest info <path to your owl directory>
{"author": ..., "title": ..., "desc": ...}
```
