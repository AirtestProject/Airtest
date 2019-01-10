Airtest
=======

**跨平台的UI自动化测试框架，适用于游戏和App**


.. image:: demo.gif


快速开始
--------

Airtest是一个跨平台的UI自动化测试框架，适用于游戏和App。目前支持Windows和Android平台，iOS支持已经发布 `Beta版`_ [`路线图`_]

Airtest提供了跨平台的API，包括安装应用、模拟输入、断言等。 基于图像识别技术定位UI元素，你无需嵌入任何代码即可进行自动化测试。 测试脚本运行后可以自动生成详细的HTML测试报告，让你迅速定位失败的测试点。

**AirtestIDE** 是一个强大的GUI工具，可以帮助你录制和调试测试脚本。 AirtestIDE给QA人员提供了完整的工作流程支持：``录制脚本->真机回放->生成报告``

`从官网开始上手吧`_


安装
----

使用 `pip` 安装Airtest框架. 

.. code:: shell

    pip install airtest

在Mac/Linux系统下，需要手动赋予adb可执行权限

.. code:: shell

    # mac系统
    cd {your_python_path}/site-packages/airtest/core/android/static/adb/mac
    # linux系统
    # cd {your_python_path}/site-packages/airtest/core/android/static/adb/linux
    chmod +x adb


如果你需要使用GUI工具，请从 `官网`_ 下载AirtestIDE。


文档
-------------

完整的Airtest框架文档请看 `readthedocs`_。


例子
-------

Airtest希望提供平台无关的API，让你的测试代码可以运行在不同平台的应用上。

1. 使用 `connect_device`_ 来连接任意Android设备或者Windows窗口。

2. 使用 `模拟操作`_ 的API来测试你的游戏或者App。

3. 千万 **不要** 忘记 `声明断言`_ 来验证测试结果。 


.. code:: python

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


更详细的说明请看 `Airtest Python API 文档`_ 或者直接看 `API代码`_ 。


用命令行运行 ``.air`` 脚本
-----------------------

使用AirtestIDE你可以非常轻松地录制一个测试脚本并保存为 ``.air`` 目录结构。
Airtest命令行则让你能够脱离IDE，在不同宿主机器和被测设备上运行测试脚本。

.. code:: shell

    # 在本地ADB连接的安卓手机上运行测试
    airtest run "path to your air dir" --device Android:///

    # 在Windows应用上运行测试
    airtest run "path to your air dir" --device "Windows:///?title_re=Unity.*"

    # 生成HTML测试报告
    airtest report "path to your air dir"

    # 也可以用python -m的方式使用命令行
    python -m airtest run "path to your air dir" --device Android:///

试试样例 ``airtest/playground/test_blackjack.air`` ，更多用法看 `命令行用法`_。


贡献代码
------------

欢迎大家fork和提pull requests。


致谢
------

感谢以下仓库让Airtest变得更好：

- `stf`_
- `atx`_
- `pywinauto`_

关于我们
-------------

访问我们的 `官网`_ 获得更多信息，同时欢迎大家扫描下方二维码关注我们的微信公众号：AirtestProject

.. image:: http://airtest.netease.com/static/img/social_media/wechat_qrcode.jpg

.. _从官网开始上手吧: http://airtest.netease.com/
.. _官网: http://airtest.netease.com/
.. _readthedocs: http://airtest.readthedocs.io/
.. _connect_device: http://airtest.readthedocs.io/en/latest/README_MORE.html#connect-device
.. _模拟操作: http://airtest.readthedocs.io/en/latest/README_MORE.html#simulate-input
.. _声明断言: http://airtest.readthedocs.io/en/latest/README_MORE.html#make-assertion
.. _Airtest Python API 文档: http://airtest.readthedocs.io/en/latest/all_module/airtest.core.api.html
.. _API reference: http://airtest.readthedocs.io/en/latest/index.html#main-api
.. _API代码: ./airtest/core/api.py
.. _命令行用法: http://airtest.readthedocs.io/en/latest/README_MORE.html#running-air-from-cli
.. _stf: https://github.com/openstf
.. _atx: https://github.com/NetEaseGame/ATX
.. _pywinauto: https://github.com/pywinauto/pywinauto
.. _路线图: https://github.com/AirtestProject/Airtest/issues/33
.. _Beta版: https://github.com/AirtestProject/iOS-Tagent
