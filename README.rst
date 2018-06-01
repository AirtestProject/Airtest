Airtest
=======

.. image:: https://travis-ci.org/AirtestProject/Airtest.svg?branch=master
    :target: https://travis-ci.org/AirtestProject/Airtest

**UI Test Automation Framework for Games and Apps**

**跨平台的UI自动化测试框架，适用于游戏和App** （`中文版点这里`_）


.. image:: demo.gif


Getting Started
---------------

Airtest is a cross-platform automated testing framework focusing mainly on games, but can also be used for native apps. Windows and Android are currently supported; iOS support is in `open beta`_ now! [`Roadmap`_]

Airtest provides cross-platform APIs, including app installation, simulated input, assertion and so forth. Airtest uses image recognition technology to locate UI elements, so that you can automate test on games without injecting any code. The test will generate an HTML report, which allows you to quickly locate failed test cases.

**AirtestIDE** is an out of the box GUI tool that helps to create and
record test cases in a user-friendly way. AirtestIDE provides QA with
a complete production workflow: ``record -> replay -> report``


`Get Started from Airtest Project Homepage`_


Installation
------------

Use `pip` to install Airtest python library. 

.. code:: shell

    pip install -U airtest


Download AirtestIDE from our `homepage`_ if you need to use the GUI tool.


Documentation
-------------

You can find the complete Airtest documentation on `readthedocs`_.


Example
-------

Airtest aims at providing platform independent API, so that you can write tests once and be able to run it on multiple devices. 

1. Using `connect_device`_ API you can connect to any android/iOS device or windows application.

2. Then perform `simulated input`_ to test your game or app. 

3. And **do not** forget to `make assertions`_ of the expected test result. 


.. code:: python

    from airtest.core.api import *

    # connect an android phone with adb
    init_device("Android")
    # or use connect_device api
    # connect_device("Android:///")

    install("path/to/your/apk")
    start_app("package_name_of_your_apk")
    touch(Template("image_of_a_button.png"))
    swipe(Template("slide_start.png"), Template("slide_end.png"))
    assert_exists(Template("success.png"))
    keyevent("BACK")
    home()
    uninstall("package_name_of_your_apk")


For more detailed info, please refer to `Airtest Python API reference`_ or take a look at `API code`_


Running ``.air`` from CLI
-------------------------

Using AirtestIDE, you can easily create and author automated tests as ``.air`` directories.
Airtest CLI provides the possibility to execute tests on different host machine and target device platforms without using AirtestIDE itself.

.. code:: shell

    # run test targeting on Android phone connected to your host machine via ADB
    airtest run "path to your .air dir" --device Android:///

    # run test targeting on Windows application whose title matches Unity.*
    airtest run "path to your .air dir" --device "Windows:///?title_re=Unity.*"

    # generate HTML report after running test
    airtest report "path to your .air dir"

    # or use as python module
    python -m airtest run "path to your .air dir" --device Android:///

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
.. _Roadmap: https://github.com/AirtestProject/Airtest/issues/33
.. _open beta: https://github.com/AirtestProject/iOS-Tagent

