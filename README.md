Airtest
================

Automated Testing Framework

# Features

*   Based on image recognition
*   Focusing on game's automation, also applicable to apps
*   Support Windows & Android, iOS support is in progress
*   Cross-Platform APIs: simulated input, assertion and report generation
*   Using AirtestIDE out of the box, providing complete production workflow: record->replay->report


# Install

```shell
git clone ssh://git@git-qa.gz.netease.com:32200/gzliuxin/airtest.git
pip install -e airtest
```


# Use as a python package

[Main API reference](./docs/_build/html/all_module/airtest.core.main.html)

```python
from airtest.core.main import *

# connect to local device with adb
connect_device("Android:///")

# start your script here
install("path/to/your/apk")
start_app("package_name_of_your_apk")
snapshot()
touch((100, 100))
touch("image_of_a_button.png")
swipe((100, 100), (200, 200))
swipe("button1.png", "button2.png")
keyevent("BACK")
home()
uninstall("package_name_of_your_apk")
```


# Use with Airtest IDE

We use `.owl` directory structure to organize code and image resources in test cases. With the help of Airtest IDE, you can easily record test cases in `.owl`. Device setup is supported by command line arguments, so you can write cross-platform code in test cases. 

```python
# To be continued...
```

# Use with command line

This command line tool is provided to run test cases without IDE on different host machines. Play CLI with the sample: ```/airtest/playground/test_blackjack.owl```

### run test case
```shell
> python -m airtest run path/to/your/owl --device Android:///
> python -m airtest run path/to/your/owl --device Android://adbhost:adbport/serialno
> python -m airtest run path/to/your/owl --device Windows:///
> python -m airtest run path/to/your/owl --device iOS:///
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
```

### generate html report
```shell
> python -m airtest report path/to/your/owl
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

### get test case info
```shell
# print in json, including: author, title and desc
> python -m airtest info path/to/your/owl
{"author": ..., "title": ..., "desc": ...}
```
