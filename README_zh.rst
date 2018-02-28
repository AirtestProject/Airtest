Airtest
=======

**跨平台的UI自动化测试框架，适用于游戏和App**


.. image:: demo.gif


快速开始
--------

Airtest是一个跨平台的UI自动化测试框架，适用于游戏和App。支持Windows和Android平台，iOS支持正在开发中。

Airtest提供了跨平台的API，包括安装应用、模拟输入、断言等。 基于图像识别技术定位UI元素，你无需嵌入任何代码即可进行自动化测试。 测试脚本运行后可以自动生成详细的HTML测试报告，让你迅速定位失败的测试点。

**AirtestIDE** 是一个强大的GUI工具，可以帮助你录制和调试测试脚本。 AirtestIDE给QA人员提供了完整的工作流程支持：``录制脚本->真机回放->生成报告``

`从官网开始上手吧`_


安装
----

使用 `pip` 安装Airtest框架. 

.. code:: shell

    pip install airtest


如果你需要使用GUI工具，请从 `官网`_ 下载AirtestIDE。


文档
-------------

完整的Airtest框架文档在`readthedocs`_。


例子
-------

Airtest希望提供平台无关的API，让你的测试代码可以运行在不同平台的应用上。

1. 使用 `connect_device`_ 来连接任意Android设备或者Windows窗口。

2. 使用 `模拟操作`_ 的API来测试你的游戏或者App。

3. 千万 **不要** 忘记 `声明断言`_ 来验证测试结果。 


.. code:: python

    from airtest.core.api import *

    # 通过ADB连接本地Android设备
    connect_device("Android:///")
    install("path/to/your/apk")
    start_app("package_name_of_your_apk")
    touch("image_of_a_button.png")
    swipe("slide_start.png", "slide_end.png")
    assert_exists("success.png")
    keyevent("BACK")
    home()
    uninstall("package_name_of_your_apk")


更详细的说明请看 `Airtest Python API 文档`_ 或者直接看 `API代码`_ 。


用命令行运行 ``.air`` 脚本
-----------------------

使用AirtestIDE你可以非常轻松地录制一个测试脚本并保存为 ``.air`` 目录结构。
Airtest命令行则让你能够脱离IDE，在不同宿主机器和被测设备上运行测试脚本。

.. code:: shell

    # run test test cases and scenarios on various devices
    > python -m airtest run <path to your air dir> --device Android:///

试试样例 ``airtest/playground/test_blackjack.air`` ，更多用法看 `命令行用法`_。


Contribution
------------

Pull requests are very welcome.


Thanks
------

Thanks for all these great works that make this project better.

- `stf`_
- `atx`_
- `pywinauto`_


.. _中文版点这里: ./README_zh.rst
.. _homepage: http://airtest.netease.com/
.. _Get Started from Airtest Project Homepage: http://airtest.netease.com/
.. _readthedocs: http://airtest.readthedocs.io/
.. _Airtest Python API reference: http://airtest.readthedocs.io/en/latest/all_module/airtest.core.api.html
.. _API reference: http://airtest.readthedocs.io/en/latest/index.html#main-api
.. _API code: ./airtest/core/api.py
.. _stf: https://github.com/openstf
.. _atx: https://github.com/NetEaseGame/ATX
.. _pywinauto: https://github.com/pywinauto/pywinauto
