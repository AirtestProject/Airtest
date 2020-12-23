# Common problems and code examples

[中文版](code_example_zh.md)

## How to initialize the script

### air script: auto_setup()

Automatically configure the interface of the running environment, you can configure the path where the current script is located, the device used, the storage path of the log content, the project root directory, and the screenshot compression accuracy:

```
auto_setup(basedir=None, devices=None, logdir=None, project_root=None, compress=None)
```

Interface example:

```python
auto_setup(__file__)

auto_setup(__file__, devices=["android://127.0.0.1:5037/emulator-5554?cap_method=JAVACAP&&ori_method=MINICAPORI&&touch_method=MINITOUCH"],
           logdir=True, project_root=r"D:\test", compress=90)
```



## How to connect/use the device

> **Please note:** For more device related information, please refer to [Document](../device/device)



### Connect the device: connect_device(URI)

The interface to connect to the device requires the URI string used to initialize the device. Example:

```python
# Connect Android device
connect_device("Android://127.0.0.1:5037/SJE5T17B17")

# Connect iOS device
connect_device("iOS:///127.0.0.1:8100")

# Connect Windows window
connect_device("Windows:///123456")

# Connect the simulator
connect_device("Android://127.0.0.1:5037/127.0.0.1:62001?cap_method=JAVACAP&&ori_method=ADBORI")
```



### Connect the device: init_device()

To initialize the interface of the device, you need to pass in the device platform, the uuid and optional parameters of the device, where uuid is the serial number of Android, the window handle of Windows, or the uuid of iOS:

```python
init_device(platform='Android', uuid=None, **kwargs)
```

Example of interface usage:

```python
# Connect Android device
init_device(platform="Android",uuid="SJE5T17B17",cap_method="JAVACAP")

# Connect Windows window
init_device(platform="Windows",uuid="123456")
```

### Get the current device: device()

Return the device instance currently in use, the usage example is as follows:

```python
dev = device()
dev.swipe_along([[959, 418],[1157, 564],[1044, 824],[751, 638],[945, 415]])
```

### Set the current device: set_current()

Set the current device used, which can be used to switch between multiple devices. Examples are as follows:

```python
# The first type: Incoming numbers 0, 1, 2, etc., switch the currently operating mobile phone to the first and second mobile phone connected to Airtest
set_current(0)
set_current(1)

# Second: Switch the current mobile phone to the serial number serialno1, serialno2
set_current("serialno1")
set_current("serialno2")
```

## How to perform coordinate click/coordinate sliding

### Coordinate click

When you click on the device, you can pass in parameters such as the click location and the number of clicks. The optional parameters under different platforms are slightly different. Examples are as follows:

```python
# Pass in absolute coordinates as the click position
touch([100,100])

# Pass in the template picture instance, click the center of the screenshot
touch(Template(r"tpl1606730579419.png", target_pos=5, record_pos=(-0.119, -0.042), resolution=(1080, 1920)))

# Click 2 times
touch([100,100],times=2)

# Under Android and Windows platforms, you can set the click duration
touch([100,100],duration=2)
```

### Coordinate sliding

For sliding operations on the device, there are two ways to pass parameters, one is to pass in the starting point and end of the sliding, and the other is to pass in the starting point and sliding direction vector. Examples are as follows:

```python
# Pass in absolute coordinates as the start and end of the sliding
swipe([378, 1460],[408, 892])

# Incoming image as a starting point, slide along a certain direction
swipe(Template(r"tpl1606814865574.png", record_pos=(-0.322, 0.412), resolution=(1080, 1920)), vector=[-0.0316, -0.3311])

# Commonly, you can also set the duration of sliding
swipe([378, 1460],[408, 892],duration=1)
```



## How to install/start/uninstall apps

### Start the application: start_app()

To start the target application on the device, you need to pass in the package name of the application, which supports Android and iOS platforms. Examples:

```python
start_app("com.netease.cloudmusic")
```

### Terminate application operation: stop_app()

To terminate the operation of the target application on the device, the package name of the application needs to be passed in. It supports Android and iOS platforms. Examples:

```python
stop_app("com.netease.cloudmusic")
```

### Clear application data: clear_app()

To clean up the target application data on the device, the package name of the application needs to be passed in. **Only supports the Android platform**, example:

```
clear_app("com.netease.cloudmusic")
```

### Install the application: install()

To install the application on the device, you need to pass in the complete apk installation path, **only supports the Android platform**, example:

```python
install(r"D:\demo\tutorial-blackjack-release-signed.apk")
```

### Uninstall the application: uninstall()

To uninstall the application on the device, you need to pass in the package name of the uninstalled application. **Only supports the Android platform**, example:

```python
uninstall("com.netease.cloudmusic")
```



## Key event: keyevent

### Android keyevent

It is equivalent to executing `adb shell input keyevent KEYNAME`, an example is as follows:

```python
keyevent("HOME")
# The constant corresponding to the home key is 3
keyevent("3") # same as keyevent("HOME")
keyevent("BACK")
keyevent("KEYCODE_DEL")
```

### Windows keyevent

Unlike Android, the Windows platform uses the `pywinauto.keyboard module` module for key input. Example:

```
keyevent("{DEL}")

# Use Alt+F4 to close the Windows window
keyevent("%{F4}")
```

### iOS keyevent

Currently only supports HOME key:

```
keyevent("HOME")
```

## How to enter text

To enter text on the device, the text box needs to be activated (that is, click the text box first, and then use the `text()` interface to enter). Examples are as follows:

```
touch (Template instance of text box)
text("input text")

# By default, text is with carriage return, you can pass False if you don’t need it
text("123",enter=False)

# Under the Android platform, you can also click the search button on the soft keyboard after typing
text("123",enter=False,search=True)
```

## How to delete text

Delete a single character through the `keyevent` interface:

```
keyevent("KEYCODE_DEL")
keyevent("67") # 67 is the delete key, please note that the input is a string
```

Simulate clearing the input box operation:

```
for i in range(10):
    keyevent("67")
```

Delete poco (leave the input box blank):

 `poco("xxx").set_text("")`.



## Log

### How to log into the report

The `log()` interface is convenient to insert some user-defined log information, which will be displayed in the Airtest report. In Airtest version 1.1.6, the log interface supports 4 parameters:

- `args`, which can be a string, a non-string or a `traceback` object;

- `timestamp`, used to customize the timestamp of the current log;

- `desc`, used to customize the title of the log;
- `snapshot`, indicating whether it is necessary to take a screenshot of the current screen image and display it in the report:

Examples are as follows:

```python
# Incoming string
log("123",desc="this is title 01")

# Pass in non-string
data = {"test": 123, "time": 123456}
log(data,desc="this is title 02")

# Incoming traceback
try:
    1/0
except Exception as e:
    log(e, desc="This is title 03")
    
# Record timestamp and take a screenshot of the current screen
log("123", timestamp=time.time(), desc="This is title 04", snapshot=True)
```

### How to set the log save path

Airtest provides some global settings, in which `LOGFILE` is used to customize the name of the txt file that records the log content; `LOGDIR` is used to customize the save path of the log content, examples are as follows:

```python
from airtest.core.settings import Settings as ST
from airtest.core.helper import set_logdir

ST.LOG_FILE = "log123.txt"
set_logdir(r'D:\test\1234.air\logs')

auto_setup(__file__)

```



### How to filter unnecessary log information

Add **settings for log information level** at the beginning of the script code:

```
__author__ = "Airtest"

import logging
logger = logging.getLogger("airtest")
logger.setLevel(logging.ERROR)
```

After changing the level of output log information to `[ERROR]`, only a small amount of initialization information is output during the entire script running process, which makes it easier to view error messages.



## Report

### Report generation: simple_report()

Simple interface for generating reports:

```python
simple_report(filepath, logpath=True, logfile='log.txt', output='log.html')
```

The 4 parameters that can be passed in represent:

- `filepath`, the path of the script file, you can directly pass in the variable `__file__``
- `logpath`, the path where the log content is located, if it is `True`, it will default to the path where the current script is located to find the log content
- `logfile`, the file path of log.txt
- `output`, the path to the report, must end with `.html`

Examples are as follows:

```python
from airtest.report.report import simple_report
auto_setup(__file__, logdir=True)

# N use case scripts are omitted here

simple_report(__file__,logpath=True,logfile=r"D:\test\1234.air\log\log.txt",output=r"D:\test\1234.air\log\log1234.html")
```



### Report generation: LogToHtml()

Base class of report:

```python
class LogToHtml(script_root, log_root=``, static_root='', export_dir=None, script_name='', logfile='log.txt', lang='en', plugins=None)
```

 The `logtohtml` class can pass in many parameters:

- `script_root`, script path
- `log_root`, the path of the log file
- `static_root`, the server path where static resources are deployed
- `export_dir`, the storage path of the export report
- `script_name`, the script name
- `logfile`, the path of the log file log.txt
- `lang`, the language of the report (Chinese: zh; English: en)
- `plugins`, plug-ins, will be used if poco or airtest-selenium is used

When using `logtohtml` to generate a test report, we generally first instantiate a `logtohtml` object, and then use this object to call the class method `report()` to generate the report. An example is as follows:

```python
from airtest.report.report import LogToHtml

# N use case scripts are omitted here

h1 = LogToHtml(script_root=r'D:\test\1234.air', log_root=r"D:\test\1234.air\log", export_dir=r"D:\test\1234.air" ,logfile= r'D:\test\1234.air\log\log.txt', lang='en', plugins=["poco.utils.airtest.report"])
h1.report()
```

## Screenshot

### How to take a screenshot with script

Take a screenshot of the target device and save it to a file. You can pass in the file name of the screenshot, a short description of the screenshot, the compression accuracy of the screenshot, and the maximum size of the screenshot. Examples are as follows:

```python
snapshot(filename="123.jpg",msg="Homepage screenshot",quality=90,max_size=800)
```

### How to take a partial screenshot

Partial screenshots or screenshots by coordinates are a frequently asked question. Airtest provides the `crop_image(img, rect)` method to help us achieve partial screenshots:

```python
# -*- encoding=utf8 -*-
__author__ = "AirtestProject"

from airtest.core.api import *
# crop_image() method is in airtest.aircv and needs to be introduced
from airtest.aircv import *

auto_setup(__file__)
screen = G.DEVICE.snapshot()

# Partial screenshot
screen = aircv.crop_image(screen,(0,160,1067,551))
# Save partial screenshots to the log folder
try_log_screen(screen)
```

### How to do partial image recognition

Steps to find a partial picture:

- Take a partial screenshot
- Define the target screenshot object to find
- Use the `match_in` method to find the specified screenshot object in the partial screenshot

```python
from airtest.core.api import *
from airtest.aircv import *
auto_setup(__file__)

screen = G.DEVICE.snapshot()
# Partial screenshot
local_screen = aircv.crop_image(screen,(0,949,1067,1500))

# Set our target screenshot as a Template object
tempalte = Template(r"png_code/settings.png")
# Find the specified image object in the partial screenshot
pos = tempalte.match_in(local_screen)

# Return the coordinates of the image object found (the coordinates are relative to the coordinates of the local screenshot)
print(pos)

# To return the coordinates of the target in the entire screen, both x and y need to be added with the minimum x and y set during the partial screenshot
print(pos[0]+0,pos[1]+949)
```

### How to set the report screenshot accuracy

`SNAPSHOT_QUALITY` is used to set the global screenshot compression accuracy, the default value is 10, and the value range is [1,100]. Examples are as follows:

```python
from airtest.core.settings import Settings as ST

# Set the global screenshot accuracy to 90
ST.SNAPSHOT_QUALITY = 90
```

Define the compression accuracy of a single screenshot, example:

```python
# Set the compression accuracy of a single screenshot to 90, and the remaining unset will be based on the global compression accuracy
snapshot(quality=90)
```


### How to set the maximum size of report screenshots

In Airtest1.1.6, a new setting for specifying the maximum size of screenshots is added: `ST.IMAGE_MAXSIZE`. If it is set to 1200, the length and width of the last saved screenshot will not exceed 1200. Example:

```python
from airtest.core.settings import Settings as ST

# Set the global screenshot size not to exceed 600*600, if not set, the default is the original image size
ST.IMAGE_MAXSIZE = 600

# In the case of not setting separately, the value of the global variable in ST is used by default, that is, 600*600
snapshot(msg="test12")
# Set the maximum size of a single screenshot not to exceed 1200*1200
snapshot(filename="test2.png", msg="test02", quality=90, max_size=1200)
```

### How to specify the path and name for saving screenshots

Take a screenshot of the screen of the current device and save the screenshot in a custom path. This can be achieved in the following ways:

```python
screen = G.DEVICE.snapshot()
pil_img = cv2_2_pil(screen)
pil_img.save(r"D:/test/首页.png", quality=99, optimize=True)
```

## How to make assertions

### Assert the existence: assert_exists()

There is an assertion target on the device screen, you need to pass in 1 assertion target (screenshot) and the assertion step information displayed on the report, example:

```python
assert_exists(Template(r"tpl1607324047907.png", record_pos=(-0.382, 0.359), resolution=(1080, 1920)), "Find the Tmall entrance on the homepage")
```


### Assert that does not exist: assert_not_exists()

There is no assertion target on the device screen. Like `assert_exists()`, you need to pass in an assertion target (screenshot) and the assertion step information displayed on the report, for example:

```python
assert_not_exists(Template(r"tpl1607325103087.png", record_pos=(-0.005, 0.356), resolution=(1080, 1920)), "The icon of Tmall Global does not exist on the current page")
```

### Assert equal: assert_equal()

To assert that two values are equal, you need to pass in the values of the two assertions, and a short description of the assertion that will be recorded in the report:

```
assert_equal("actual value", "predicted value", "please fill in a short description of the assertion")
```

It is often used to make an assertion together with the script that poco gets the attribute. Examples are as follows:

```python
assert_equal(poco("com.taobao.taobao:id/dx_root").get_text(), "Tmall new product", "The text attribute value of the control is Tmall new product")

assert_equal(str(poco(text="Tmall new product").attr("enabled")), "True", "The enabled attribute value of the control is True")
```

### Assert that is not equal: assert_not_equal()

Assert that two values are not equal, like `assert_equal()`, you need to pass in the values of 2 assertions, and a short description of the assertion that will be recorded in the report:

```python
assert_not_equal("actual value", "predicted value", "please fill in a short description of the assertion")

assert_not_equal("1", "2", "Assert that 1 and 2 are not equal")
```



## How to switch between absolute and relative coordinates

Use code to switch between absolute coordinates and relative coordinates:

```python
# Get device screen resolution (vertical screen)
height = G.DEVICE.display_info['height']
width = G.DEVICE.display_info['width']

# Known absolute coordinates [311,1065], converted to relative coordinates
x1 = 311/width
y1 = 1065/height
poco.click([x1,y1])

# Known relative coordinates [0.3,0.55], convert to absolute coordinates
x2 = 0.3*width
y2 = 0.55*height
touch([x2,y2])

# If it is a horizontal screen device, the resolution is as follows
height = G.DEVICE.display_info['width']
width = G.DEVICE.display_info['height']
```

Determine whether the current screen is horizontal or vertical, and get the resolution of the current screen:

```python
if G.DEVICE.display_info['orientation'] in [1,3]:
    height = G.DEVICE.display_info['width']
    width = G.DEVICE.display_info['height']
else:
    height = G.DEVICE.display_info['height']
    width = G.DEVICE.display_info['width']
```

## How to call other .air scripts

If you want to call a public function encapsulated in another `.air` script in a `.air` script, you can do this:

```python
from airtest.core.api import using
# Relative path or absolute path, make sure the code can be found
using("common.air")

from common import common_function
common_function()
```

If the paths of the sub-scripts that need to be referenced are all placed in a certain directory, you can set a default project root directory `PROJECT_ROOT`, so that when using the `using` interface, you can find other sub-scripts in the current root directory without filling in The full path makes it easier to call each other between scripts.

For example, if we create a script named `test1.air`, the actual path is `/User/test/project/test1.air`:

```python
from airtest.core.api import *

def test():
    touch("tmp.png")
```

Another `main.air` script in the same directory can refer to the `test` in it like this:

```python
from airtest.core.api import *

ST.PROJECT_ROOT = "/User/test/project"
using("test1.air")
from test1 import test
```


## How to record screen during script running

Currently only supports screen recording on Android devices, please refer to [Record the screen while running the script](../device/android.html#record-the-screen-while-running-the-script)
