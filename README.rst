Airtest
=======

**UI Test Automation Framework for Games and Apps**

**跨平台的UI自动化测试框架，适用于游戏和App** （`中文版点这里`_）


.. image:: demo.gif


Getting Started
---------------

Airtest is a cross-platform automated testing framework with main focus on games,
which can also be used for native apps. Currently, Windows and Android are well supported.
Support for iOS comes in near future.

Airtest provides cross-platform APIs, including app installation, simulated input, assertion and so forth. Airtest uses image recognition technology to locate UI elements, so that you can automate test on games without injecting any code. After running the test, an HTML report will be generated automatically, that allows you to quickly locate failed test points.

**AirtestIDE** is an out of the box GUI tool that helps to create and
record test cases in the user-friendly way. AirtestIDE provides QA with
a complate production workflow: ``record -> replay -> report``


`Get Started from Airtest Project Homepage`_


Installation
------------

Use `pip` to install Airtest python library. 

.. code:: shell

    pip install airtest


Download AirtestIDE from our `homepage`_ if you need to use the GUI tool.


Documentation
-------------

You can find the complete airtest documentation on `readthedocs`_.


Example
-------

Airtest aims at providing platform independent api, so that you can write test once and run test on different devices.

1. Using `connect_device`_ API you can connect to any android device or windows application. 

2. Then perform `simulated input`_ to test your game or app. 

3. And **do not** forget to `make assertions`_ of the expected test result. 


.. code:: python

    from airtest.core.api import *

    # connect an android phone with adb
    connect_device("Android:///")
    install("path/to/your/apk")
    start_app("package_name_of_your_apk")
    touch("image_of_a_button.png")
    swipe("slide_start.png", "slide_end.png")
    assert_exists("success.png")
    keyevent("BACK")
    home()
    uninstall("package_name_of_your_apk")


For more detailed info, please refer to `Airtest Python API reference`_ or take a look at `API code`_


Running ``.air`` from CLI
-------------------------

Using AirtestIDE, you can easily create and author automated tests as ``.air`` directories.
Airtest CLI provides the possibility to execute tests on different host machine and target device platforms without using AirtestIDE itself.

.. code:: shell

    python -m airtest run <path to your air dir> --device Android:///
    python -m airtest run <path to your air dir> --device Windows:///?title_re=Unity.*

Try running provided test case: ``airtest/playground/test_blackjack.air`` and see `Usage of CLI`_.


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
.. _connect_device: http://airtest.readthedocs.io/en/latest/README_MORE.html#connect-device
.. _simulated input: http://airtest.readthedocs.io/en/latest/README_MORE.html#simulate-input
.. _make assertions: http://airtest.readthedocs.io/en/latest/README_MORE.html#make-assertion
.. _Airtest Python API reference: http://airtest.readthedocs.io/en/latest/all_module/airtest.core.api.html
.. _API reference: http://airtest.readthedocs.io/en/latest/index.html#main-api
.. _API code: ./airtest/core/api.py
.. _Usage of CLI: http://airtest.readthedocs.io/en/latest/README_MORE.html#running-air-from-cli
.. _stf: https://github.com/openstf
.. _atx: https://github.com/NetEaseGame/ATX
.. _pywinauto: https://github.com/pywinauto/pywinauto
