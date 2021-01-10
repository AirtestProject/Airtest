# 常见问题与代码示例

[English version](code_example.md)

## 如何进行脚本初始化
### air脚本：auto_setup()
自动配置运行环境的接口，可以配置当前脚本所在路径、使用的设备、log内容的保存路径、项目根目录和截图压缩精度：

```
auto_setup(basedir=None, devices=None, logdir=None, project_root=None, compress=None)
```
接口示例：

```
auto_setup(__file__)

auto_setup(__file__, devices=["android://127.0.0.1:5037/emulator-5554?cap_method=JAVACAP&&ori_method=MINICAPORI&&touch_method=MINITOUCH"], logdir=True, project_root=r"D\test", compress=90)
```

## 如何连接/使用设备

> **请注意：** 更多设备相关的信息，请参考[文档](../device/device)



### 连接设备：connect_device(URI)
连接设备的接口，需要传入用于初始化设备的URI字符串，示例：

```
# 连接安卓设备
connect_device("Android://127.0.0.1:5037/SJE5T17B17")

# 连接iOS设备
connect_device("iOS:///127.0.0.1:8100")

# 连接Windows窗口
connect_device("Windows:///123456")

# 连接模拟器
connect_device("Android://127.0.0.1:5037/127.0.0.1:62001?cap_method=JAVACAP&&ori_method=ADBORI")
```

### 连接设备：init_device()
初始化设备的接口，需要传入设备平台、设备的uuid和可选参数等，其中uuid为，Android的序列号，Windows的窗口句柄，或iOS的uuid：

```
init_device(platform='Android', uuid=None, **kwargs)
```
接口使用示例：

```
# 连接安卓设备
init_device(platform="Android",uuid="SJE5T17B17",cap_method="JAVACAP")

# 连接Windows窗口
init_device(platform="Windows",uuid="123456")
```

### 获取当前设备：device()
返回当前正在使用中的设备实例，用法示例如下：

```
dev = device()
dev.swipe_along([[959, 418],[1157, 564],[1044, 824],[751, 638],[945, 415]])
```

### 设置当前设备：set_current()
设置当前的使用设备，可以用于在多设备之间切换使用，示例如下：

```
# 第一种：传入数字0、1、2等，切换当前操作的手机到Airtest连接的第1台、第2台手机
set_current(0)
set_current(1)

# 第二种：切换当前操作的手机到序列号为serialno1、serialno2的手机
set_current("serialno1")
set_current("serialno2")
```

## 如何进行坐标点击/坐标滑动

### 坐标点击

在设备上进行点击操作，可以传入点击位置、点击次数等参数，不同平台下的可选参数稍有不同，示例如下：

```
# 传入绝对坐标作为点击位置
touch([100,100])

# 传入Template图片实例，点击截图中心位置
touch(Template(r"tpl1606730579419.png", target_pos=5, record_pos=(-0.119, -0.042), resolution=(1080, 1920)))

# 点击2次
touch([100,100],times=2)

# Android和Windows平台下，可以设置点击时长
touch([100,100],duration=2)
```

### 坐标滑动

在设备上进行滑动操作，有2种传参方式，一种是传入滑动的起点和终点，一种是传入滑动的起点和滑动方向vector，示例如下：

```
# 传入绝对坐标作为滑动的起点和终点
swipe([378, 1460],[408, 892])

# 传入图像作为起点，沿着某个方向滑动
swipe(Template(r"tpl1606814865574.png", record_pos=(-0.322, 0.412), resolution=(1080, 1920)), vector=[-0.0316, -0.3311])

# 常见的还可以设置滑动的持续时长
swipe([378, 1460],[408, 892],duration=1)
```

## 如何安装/启动/卸载应用

### 启动应用：start_app()
在设备上启动目标应用，需传入应用的包名，支持Android和iOS平台，示例：

```
start_app("com.netease.cloudmusic")
```

### 终止应用运行：stop_app()
在设备上终止目标应用的运行，需传入应用的包名，支持Android和iOS平台，示例：

```
stop_app("com.netease.cloudmusic")
```

### 清除应用数据：clear_app()
清理设备上的目标应用数据，需传入应用的包名，**仅支持Android平台** ，示例：

```
clear_app("com.netease.cloudmusic")
```

### 安装应用：install()
安装应用到设备上，需传入完整的apk的安装路径，**仅支持Android平台**，示例：
```
install(r"D:\demo\tutorial-blackjack-release-signed.apk")
```

### 卸载应用：uninstall()

卸载设备上的应用，需传入被卸载应用的包名，**仅支持Android平台**，示例：

```
uninstall("com.netease.cloudmusic")
```

## 按键事件：keyevent

### Android的keyevent

等同于执行 `adb shell input keyevent KEYNAME` ，示例如下：

```
keyevent("HOME")
# The constant corresponding to the home key is 3
keyevent("3")  # same as keyevent("HOME")
keyevent("BACK")
keyevent("KEYCODE_DEL")
```

### Windows的keyevent
与安卓不同，Windows平台使用 `pywinauto.keyboard module` 模块来进行按键输入，示例：  

```
keyevent("{DEL}")

# 使用Alt+F4关闭Windows窗口
keyevent("%{F4}")
```
### iOS的keyevent

目前仅支持HOME键：
```
keyevent("HOME")
```

## 如何输入文本
在设备上输入文本，文本框需要处于激活状态（即先点击文本框，再使用 `text()` 接口进行输入）。示例如下：

```
touch(文本框的Template实例)
text("输入的文本")

# 默认情况下，text是带回车的，不需要可以传入False
text("123",enter=False)

# 安卓平台下，还支持输入后点击软键盘的搜索按钮
text("123",enter=False,search=True)
```

## 如何删除文本
通过 `keyevent` 接口删除单个字符:
```
keyevent("KEYCODE_DEL")
keyevent("67")  # 67即为删除键，请注意传入的是字符串
```
模拟清空输入框操作:
```
for i in range(10):
    keyevent("67")
```

poco的删除（输入框置空）：

 `poco("xxx").set_text("")` 。

## log相关

### 如何记录log到报告中

`log()` 接口方便插入用户自定义的一些log信息，将会被显示在Airtest报告中。在1.1.6版本的Airtest中，log接口支持传入4个参数：
- `args` ，可以是字符串、非字符串或者 `traceback` 对象
- `timestamp` ，用于自定义当前log的时间戳
- `desc` ，用于自定义log的标题
- `snapshot` ，表示是否需要截取一张当前的屏幕图像并显示到报告中

示例如下：  
```
# 传入字符串
log("123",desc="这是标题01")

# 传入非字符串
data = {"test": 123, "time": 123456}
log(data,desc="这是标题02")

# 传入traceback
try:
    1/0
except Exception as e:
    log(e, desc="这是标题03")
    
# 记录timestamp，并且对当前画面截图
log("123", timestamp=time.time(), desc="这是标题04", snapshot=True)
```
### 如何设置log的保存路径

Airtest提供了一些全局的设置，其中 `LOGFILE` 用于自定义记录log内容的txt文档的名称；`LOGDIR` 用于自定义log内容的保存路径，示例如下：

```
from airtest.core.settings import Settings as ST
from airtest.core.helper import set_logdir

ST.LOG_FILE = "log123.txt"
set_logdir(r'D:\test\1234.air\logs')

auto_setup(__file__)

```

### 如何过滤不必要的log信息
在脚本代码开头加上 **对日志信息等级的设定**：

```
__author__ = "Airtest"

import logging
logger = logging.getLogger("airtest")
logger.setLevel(logging.ERROR)
```
把输出日志信息的级别改成 `[ERROR]` 以后，整个脚本运行过程中只有少量初始化信息输出，更方便查看报错信息。

## 报告

### 报告生成：simple_report()  

生成报告的简单接口：

```
simple_report(filepath, logpath=True, logfile='log.txt', output='log.html')
```

其中可传入的4个参数分别表示：

- `filepath`，脚本文件的路径，可以直接传入变量 `__file__` 
- `logpath` ，log内容所在路径，如为 `True` ，则默认去当前脚本所在路径找log内容
- `logfile` ，log.txt的文件路径
- `output` ，报告的到处路径，必须以 `.html` 结尾

示例如下：

```
from airtest.report.report import simple_report
auto_setup(__file__, logdir=True)

# 此处省略N条用例脚本

simple_report(__file__,logpath=True,logfile=r"D:\test\1234.air\log\log.txt",output=r"D:\test\1234.air\log\log1234.html")
```

### 报告生成：LogToHtml()

报告的基类：

```
class LogToHtml(script_root, log_root='', static_root='', export_dir=None, script_name='', logfile='log.txt', lang='en', plugins=None)
```

 `logtohtml` 类可以传入的参数非常多：

- `script_root` ，脚本路径
- `log_root` ，log文件的路径
- `static_root` ，部署静态资源的服务器路径
- `export_dir` ，导出报告的存放路径
- `script_name` ，脚本名称
- `logfile` ，log文件log.txt的路径
- `lang` ，报告的语言（中文：zh；英文：en）
- `plugins` ，插件，使用了poco或者airtest-selenium会用到

使用 `logtohtml` 生成测试报告时，我们一般先实例化一个 `logtohtml` 对象，然后用这个对象调用类方法 `report()` 生成报告，示例如下： 

```
from airtest.report.report import LogToHtml

# 此处省略N条用例脚本

h1 = LogToHtml(script_root=r'D:\test\1234.air', log_root=r"D:\test\1234.air\log", export_dir=r"D:\test\1234.air" ,logfile=r'D:\test\1234.air\log\log.txt', lang='en', plugins=["poco.utils.airtest.report"])
h1.report()
```

## 截图相关

### 如何用脚本截图
对目标设备进行一次截图，并且保存到文件中，可以传入截图文件名、截图的简短描述、截图压缩精度和截图最大尺寸，示例如下：

```
snapshot(filename="123.jpg",msg="首页截图",quality=90,max_size=800)
```

### 如何进行局部截图
局部截图或者说按坐标截图是大家经常会问到的问题，Airtest提供了 `crop_image(img, rect)` 方法可以帮助我们实现局部截图：   

```
# -*- encoding=utf8 -*-
__author__ = "AirtestProject"

from airtest.core.api import *
# crop_image()方法在airtest.aircv中，需要引入
from airtest.aircv import *

auto_setup(__file__)
screen = G.DEVICE.snapshot()

# 局部截图
screen = aircv.crop_image(screen,(0,160,1067,551))
# 保存局部截图到log文件夹中
try_log_screen(screen)
```
### 如何做局部识图

局部找图的步骤：
- 进行局部截图
- 定义要查找的目标截图对象
- 利用 `match_in` 方法，在局部截图中查找指定的截图对象
```
from airtest.core.api import *
from airtest.aircv import *
auto_setup(__file__)

screen = G.DEVICE.snapshot() 
# 局部截图
local_screen = aircv.crop_image(screen,(0,949,1067,1500))

# 将我们的目标截图设置为一个Template对象
tempalte = Template(r"png_code/设置.png")
# 在局部截图里面查找指定的图片对象
pos = tempalte.match_in(local_screen)

# 返回找到的图片对象的坐标（该坐标是相对于局部截图的坐标）
print(pos)

# 若要返回目标在整个屏幕中的坐标，则x，y都需要加上局部截图时设置的最小x、y
print(pos[0]+0,pos[1]+949)
```


### 如何设置报告的截图精度

`SNAPSHOT_QUALITY` 用于设置全局的截图压缩精度，默认值为10，取值范围[1,100]。示例如下：

```
from airtest.core.settings import Settings as ST

# 设置全局的截图精度为90
ST.SNAPSHOT_QUALITY = 90
```

定义单张截图的压缩精度，示例：

```
# 设置单张截图的压缩精度为90，其余未设置的将按照全局压缩精度来
snapshot(quality=90)
```


### 如何设置报告截图的最大尺寸

在Airtest1.1.6中，新增了一个用于指定截图最大尺寸的设置：`ST.IMAGE_MAXSIZE` 。假如设置为1200，则最后保存的截图长宽都不会超过1200，示例：

```
from airtest.core.settings import Settings as ST

# 设置全局截图尺寸不超过600*600，如果不设置，默认为原图尺寸
ST.IMAGE_MAXSIZE = 600

# 不单独设置的情况下，默认采用ST中的全局变量的数值，即600*600
snapshot(msg="test12")
# 设置单张截图的最大尺寸不超过1200*1200
snapshot(filename="test2.png", msg="test02", quality=90, max_size=1200) 
```

### 如何指定截图保存的路径和名称
对当前设备的屏幕进行截图，并将截图保存在自定义路径下，可以用下述方式实现：
```
screen = G.DEVICE.snapshot()  
pil_img = cv2_2_pil(screen)
pil_img.save(r"D:/test/首页.png", quality=99, optimize=True)
```

## 如何做断言

### 断言存在：assert_exists()

设备屏幕上存在断言目标，需要传入1个断言目标（截图）和在报告上显示的断言步骤信息，示例：

```
assert_exists(Template(r"tpl1607324047907.png", record_pos=(-0.382, 0.359), resolution=(1080, 1920)), "找到首页的天猫入口")  
```


### 断言不存在：assert_not_exists()

设备屏幕上不存在断言目标，与 `assert_exists()` 一样，需要传入1个断言目标（截图）和在报告上显示的断言步骤信息，示例：

```
assert_not_exists(Template(r"tpl1607325103087.png", record_pos=(-0.005, 0.356), resolution=(1080, 1920)), "当前页不存在天猫国际的icon")  
```


### 断言相等：assert_equal()

断言两个值相等，需要传入2个断言的值，还有将被记录在报告中的断言的简短描述：

```
assert_equal("实际值", "预测值", "请填写断言的简短描述")
```

常与poco获取属性的脚本一起做断言，示例如下：

```
assert_equal(poco("com.taobao.taobao:id/dx_root").get_text(), "天猫新品", "控件的text属性值为天猫新品")

assert_equal(str(poco(text="天猫新品").attr("enabled")), "True", "控件的enabled属性值为True")
```

### 断言不相等：assert_not_equal()
断言两个值不相等，与 `assert_equal()` 一样，需要传入2个断言的值，还有将被记录在报告中的断言的简短描述：

```
assert_not_equal("实际值", "预测值", "请填写断言的简短描述")

assert_not_equal("1", "2", "断言1和2不相等")
```

## 如何切换绝对坐标和相对坐标

用代码实现绝对坐标和相对坐标之间的切换：  
```
# 获取设备屏幕分辨率(竖屏)
height = G.DEVICE.display_info['height']
width = G.DEVICE.display_info['width']

# 已知绝对坐标[311,1065]，转换成相对坐标
x1 = 311/width
y1 = 1065/height
poco.click([x1,y1])

# 已知相对坐标[0.3,0.55]，转换成绝对坐标
x2 = 0.3*width
y2 = 0.55*height
touch([x2,y2])

# 如果是横屏设备的话，则分辨率如下
height = G.DEVICE.display_info['width']
width = G.DEVICE.display_info['height']
```

判断当前屏幕为横屏还是竖屏，并获取当前屏幕的分辨率：  

```
if G.DEVICE.display_info['orientation'] in [1,3]:
    height = G.DEVICE.display_info['width']
    width = G.DEVICE.display_info['height']
else:
    height = G.DEVICE.display_info['height']
    width = G.DEVICE.display_info['width']
```

## 如何调用别的.air脚本

如果想要在一个`.air` 脚本中，调用另外一个 `.air` 脚本里封装的公用函数，可以这样做:

```
from airtest.core.api import using
# 相对路径或绝对路径，确保代码能够找得到即可
using("common.air")

from common import common_function
common_function()
```

如果需要引用的子脚本路径统一都放在某个目录下，可以通过设定一个默认项目根目录 `PROJECT_ROOT` ，让使用 `using` 接口时能够在当前根目录下寻找别的子脚本，无需填写完整路径，让脚本之间相互调用使用更加方便。

例如，我们建立一个名为 `test1.air` 的脚本，实际路径为 `/User/test/project/test1.air` :

```
from airtest.core.api import *

def test():
    touch("tmp.png")
```

在同一目录下另外一个 `main.air` 脚本可以这样引用到它里面的 `test` :

```
from airtest.core.api import *

ST.PROJECT_ROOT = "/User/test/project"
using("test1.air")
from test1 import test
```

## 如何在脚本运行过程中录制屏幕

目前仅支持Android设备的录屏，请参见[在运行脚本过程中录屏](../device/android_zh.html#id13)
