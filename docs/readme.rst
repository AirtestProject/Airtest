



================
Insrtall
================

自动化测试框架
================

*   基于图像匹配，适合做游戏的自动化测试，同样也可以用作App
*   支持Windows/Android/iOS
*   提供[IDE](http://init.nie.netease.com/airtest_home/)，0上手成本，支持完整的工作流程：录制、回放、生成报告
*   同样作为Python库，可以用作其他测试框架的底层，提供跨平台的模拟操作、断言、报告生成等功能


Development
================

1. 安装aircv
--------------

::

    git clone -b open-source ssh://git@git-qa.gz.netease.com:32200/airtest-projects/aircv.git
    pip install -e aircv


1. 安装airtest
--------------
::
    
    git clone ssh://git@git-qa.gz.netease.com:32200/gzliuxin/airtest.git
    pip install -e airtest


Use as a python package
^^^^^^^^^^^^^^^^^^^^^^^^

::

    from airtest.core.main import *

    # init a android device, adb connection required
    set_serialno()

    # start your script here
    aminstall("path/to/your/apk")
    amstart("package_name_of_your_apk")
    snapshot()
    touch((100, 100))
    touch("picture_of_a_button.png")
    swipe((100, 100), (200, 200))
    keyevent("BACK")
    home()
    uninstall("package_name_of_your_apk")



命令行工具
^^^^^^^^^^^^
因为脚本中包含图片资源，所以我们设计了.owl的目录结构，用IDE可以方便地录制.owl脚本。为了不依赖IDE运行脚本，同时支持跨平台运行，我们提供了命令行工具：将设备初始化、配置等平台相关操作用命令行参数传入，脚本中只包含平台无关的操作逻辑和断言。

::

    // 使用方法
    > python -m airtest -h
    // 运行脚本
    > python -m airtest run
    // 生成报告
    > python -m airtest report
    // 获取脚本信息
    > python -m airtest info
