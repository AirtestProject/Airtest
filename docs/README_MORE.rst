Airtest
=======

**Cross-Platform UI Automation Framework for Games and Apps**


.. raw:: html

    <div style=" overflow: hidden; max-width: 100%; height: auto;">
        <div align="center" class="embed-responsive embed-responsive-16by9">
            <video class="embed-responsive-item device-record" autoplay loop controls="none" style="top: 0;bottom: 0;left: 0;width: 100%;height: 100%;border: 0;">
                <source src="./demo.mp4" type="video/mp4">
            </video>
        </div>
        <br/>
    </div>


Getting Started
---------------

*   **Cross-Platform:** Airtest automates games and apps on almost all platforms.

*   **Write Once, Run Anywhere:** Airtest provides cross-platform APIs, including app installation, simulated input, assertion and so forth. Airtest uses image recognition technology to locate UI elements, so that you can automate games and apps without injecting any code. 

*   **Fully Scalable:** Airtest cases can be easily run on large device farms, using commandline or python API. HTML reports with detailed info and screen recording allow you to quickly locate failure points. NetEase builds [Airlab](https://airlab.163.com/) on top of Airtest Project.

*   **AirtestIDE:** AirtestIDE is an out of the box GUI tool that helps to create and run cases in a user-friendly way. AirtestIDE supports a complete automation workflow: ``create -> run -> report``.

`Get Started from Airtest Project Homepage`_


Supported Platforms
...................

-  Android
-  iOS
-  Windows
-  Unity
-  Cocos2dx
-  Egret
-  WeChat


Installation
------------

This section describes how to install Airtest python library.
Download AirtestIDE from our `homepage`_ if you need to use the GUI tool.


System Requirements
...................

-  Operating System:

   -  Windows
   -  MacOS X
   -  Linux

-  Python2.7 & Python3.3+


Installing the python package
..............................

Airtest package can be installed directly from Pypi. Use
``pip`` to manage installation of all python dependencies and package
itself.

.. code:: shell

    pip install -U airtest


You can also install it from Git repository.

.. code:: shell

    git clone https://github.com/AirtestProject/Airtest.git
    pip install -e airtest


Use ``-e`` here to install airtest in develop mode since this repo is in
rapid development. Then you can upgrade the repo with ``git pull``
later.


Documentation
-------------

You can find the complete Airtest documentation on `readthedocs`_.


Example
------------

Airtest provides simple APIs that are platform independent. This section
describes how to create an automated case which does the following:

1. connects to local android device with ``adb``
2. installs the ``apk`` application
3. runs application and takes the screenshot
4. performs several user operations (touch, swipe, keyevent)
5. uninstalls application

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


Basic Usage
------------

Airtest aims at providing platform independent API, so that you can write automated cases once and run it on multiple devices and platforms.

1. Using `connect_device`_ API you can connect to any android/iOS device or windows application. 

2. Then perform `simulated input`_ to automate your game or app. 

3. **DO NOT** forget to `make assertions`_ of the expected result. 


Connect Device
...............

Using ``connect_device`` API you can connect to any android/iOS device or windows application.

.. code:: python

    connect_device("platform://host:port/uuid?param=value&param2=value2")

- platform: Android/iOS/Windows...

- host: adb host for android, iproxy host for iOS, empty for other platforms

- port: adb port for android, iproxy port for iOS, empty for other platforms

- uuid: uuid for target device, e.g. serialno for Android, handle for Windows, uuid for iOS

- param: device initialization configuration fields. e.g. cap_method/ori_method/...

- value: device initialization configuration field values.


see also `connect_device`_.

Connect android device
***********************

1. Connect your android phone to your PC with usb
2. Use ``adb devices`` to make sure the state is ``device``
3. Connect device in Airtest
4. If you have multiple devices or even remote devices, use more params to specify the device

.. code:: python

    # connect an android phone with adb
    init_device("Android")

    # or use connect_device api with default params
    connect_device("android:///")

    # connect a remote device using custom params
    connect_device("android://adbhost:adbport/1234566?cap_method=javacap&touch_method=adb")

Connect iOS device
******************

Follow the instruction of `iOS-Tagent`_ to setup the environment.

.. code:: python

    # connect a local ios device
    connect_device("ios:///")

Connect windows application
****************************

.. code:: python

    # connect local windows desktop
    connect_device("Windows:///")

    # connect local windows application
    connect_device("Windows:///?title_re=unity.*")


Airtest uses `pywinauto` as Windows backend. For more window searching params, please see `pywinauto documentation`_.


Simulate Input
...............

Following APIs are fully supported:

- touch
- swipe
- text
- keyevent
- snapshot
- wait

More APIs are available, some of which may be platform specific, please see `API reference`_ for more information.


Make Assertion
...............

Airtest provide some assert functions, including:

- assert_exists
- assert_not_exists
- assert_equal
- assert_not_equal

When assertion fails, it will raise ``AssertsionError``. And you will see all assertions in the html report.


Running ``.air`` from CLI
-----------------------------------

Using AirtestIDE, you can easily create and author automated cases as ``.air`` directories.
Airtest CLI provides the possibility to execute cases on different host machine and target device platforms without using AirtestIDE itself.

Connections to devices are specified by command line arguments, i.e. the code is platform independent and one automated case can be used for Android, iOS or Windows apps as well. 

Following examples demonstrate the basic usage of airtest framework running from CLI. For a deeper understanding, try running provided automated cases: ``airtest/playground/test_blackjack.air``


run automated case
..............
.. code:: shell

    # run automated cases and scenarios on various devices
    > airtest run "path to your .air dir" --device Android:///
    > airtest run "path to your .air dir" --device Android://adbhost:adbport/serialno
    > airtest run "path to your .air dir" --device Windows:///?title_re=Unity.*
    > airtest run "path to your .air dir" --device iOS:///
    ...
    # show help
    > airtest run -h
    usage: airtest run [-h] [--device [DEVICE]] [--log [LOG]]
                       [--recording [RECORDING]]
                       script

    positional arguments:
      script                air path

    optional arguments:
      -h, --help            show this help message and exit
      --device [DEVICE]     connect dev by uri string, e.g. Android:///
      --log [LOG]           set log dir, default to be script dir
      --recording [RECORDING]
                          record screen when running


generate html report
.....................
.. code:: shell

    > airtest report "path to your .air dir"
    log.html
    > airtest report -h
    usage: airtest report [-h] [--outfile OUTFILE] [--static_root STATIC_ROOT]
                          [--log_root LOG_ROOT] [--record RECORD [RECORD ...]]
                          [--export EXPORT] [--lang LANG]
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
      --record RECORD [RECORD ...]
                            custom screen record file path
      --export EXPORT       export a portable report dir containing all resources
      --lang LANG           report language


get case info
...................
.. code:: shell

    # print case info in json if defined, including: author, title, desc
    > python -m airtest info "path to your .air dir"
    {"author": ..., "title": ..., "desc": ...}


Import from other ``.air``
--------------------------
You can write some common used function in one ``.air`` script and import it from other scripts. Airtest provide ``using`` API to manage the context change including ``sys.path`` and ``Template`` search path.

.. code:: python

    from airtest.core.api import using
    using("common.air")

    from common import common_function

    common_function()


.. _Get Started from Airtest Project Homepage: http://airtest.netease.com/
.. _homepage: http://airtest.netease.com/
.. _readthedocs: http://airtest.readthedocs.io/
.. _pywinauto documentation: https://pywinauto.readthedocs.io/en/latest/code/pywinauto.findwindows.html#pywinauto.findwindows.find_elements
.. _simulated input: http://airtest.readthedocs.io/en/latest/README_MORE.html#simulate-input
.. _iOS-Tagent: https://github.com/AirtestProject/iOS-Tagent
.. _make assertions: http://airtest.readthedocs.io/en/latest/README_MORE.html#make-assertion
.. _Airtest Python API reference: http://airtest.readthedocs.io/en/latest/all_module/airtest.core.api.html
.. _API reference: http://airtest.readthedocs.io/en/latest/index.html#main-api
.. _API code: ./airtest/core/api.py
.. _connect_device: https://airtest.readthedocs.io/en/latest/all_module/airtest.core.api.html#airtest.core.api.connect_device
.. _AirLab: https://airlab.163.com
