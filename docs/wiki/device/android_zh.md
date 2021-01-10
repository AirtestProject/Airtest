# Android设备连接方法与常见代码示例

[English version](android.md)

## Android手机连接

若使用AirtestIDE进行手机连接，请参考[文档](https://airtest.doc.io.netease.com/IDEdocs/device_connection/1_android_phone_connection/)

若不打算使用AirtestIDE，可以参考以下步骤：

- 打开手机中的 **开发者选项** , 以及 **允许USB调试**
- 使用USB连上手机后，能够使用`adb devices`命令看到设备，参考[使用ADB查看手机是否成功连接](#使用ADB查看手机是否成功连接)
- 在代码和命令行中，使用手机序列号连接手机，参见[在代码中使用手机](#在代码中使用手机)


### 使用ADB查看手机是否成功连接

`adb`是谷歌官方推出的Android命令行工具，可以让我们跟设备进行通信。（感兴趣的话，请参考：[官方地址](https://developer.android.com/studio/command-line/adb)。）

我们已经在`airtest\airtest\core\android\static\adb`目录下，存放了各平台的`adb`可执行文件，大家无需下载也可以使用。

以windows为例，可以先使用终端进入到`adb.exe`所在的目录下（在`airtest\airtest\core\android\static\adb\windows`目录下shift+右键打开命令行终端），然后执行`adb devices`命令行：

```
E:\airtest\airtest\core\android\static\adb\windows>adb devices

List of devices attached
c2b1c2a7        device
eba17551        device
127.0.0.1:10033 device
```

在mac中，可以访问`airtest/core/android/static/adb/mac`目录下，运行 `./adb devices`，若提示adb没有可执行权限，可以运行`chmod +x adb`为它添加可执行权限。

- 在上面这个例子中，可以看到当前连接的3台Android设备，状态为`device`就是正常在线
- 如果设备状态为`unauthorized`，请在手机上弹出的`允许USB调试`菜单中点击同意
- 如果看不到设备名称，可能需要在PC上安装手机对应的官方驱动

### 手机连接遇到问题

由于手机对应的厂商和型号各不相同，可能在连接过程中会遇到各种各样的问题，请参考[Android连接常见问题](https://airtest.doc.io.netease.com/IDEdocs/device_connection/2_android_faq/)

### 在代码中使用手机

确认手机能够成功连接后，我们能够在`adb devices`命令行的结果中看到手机的设备序列号：

```
> adb devices

List of devices attached
c2b1c2a7        device
```

上面的`c2b1c2a7`就是手机的设备序列号，我们用以下格式的字符串来定义一台手机：

```
Android://<adbhost>:<adbport>/<serialno>
```

其中：

- `adbhost`是adb server所在主机的ip，默认是本机，也就是`localhost`或`127.0.0.1`
- `adb port`默认是5037
- `serialno`是android手机的序列号，例如刚才的`c2b1c2a7`

以下是一些示例：

```
# 什么都不填写，会默认取当前连接中的第一台手机
Android:///
# 连接本机默认端口连的一台设备号为c2b1c2a7的手机
Android://127.0.0.1:5037/c2b1c2a7
# 用本机的adb连接一台adb connect过的远程设备，注意10.254.60.1:5555其实是serialno
Android://127.0.0.1:5037/10.254.60.1:5555
```

#### 根据Android:///字符串连接手机

当我们使用命令行运行脚本时，可以使用`--device Android:///`来为它指定脚本运行的Android设备，例如：

```
>airtest run untitled.air --device Android:///手机序列号 --log log/
```

除此之外，当我们想在代码里连接手机时，可以使用`connect_device`接口：

```
from airtest.core.api import *
connect_device("Android:///手机序列号")
```

这两种方式只需要选择其中一种，基本上都能满足我们连接设备的需求。


#### 一些特殊参数

部分特殊设备在连接时可能会出现黑屏的情况，例如一些模拟器，我们可以额外添加`cap_method=JAVACAP`的参数来强制指定屏幕截图方式为`JAVACAP`:

```
# 连接了模拟器，勾选了`Use javacap`模式
Android://127.0.0.1:5037/127.0.0.1:7555?cap_method=JAVACAP
```

除此之外，我们还有另外两个参数，分别是用于指定设备画面旋转模式的`ori_method=ADBORI`，以及指定点击画面方式为ADB指令点击的`touch_method=ADBTOUCH`。

大部分情况下，我们无需指定这些参数，只有在一些特殊的Android设备（例如部分特殊型号的平板）上，使用默认参数无法连接时，才需要加入额外的参数：

```
# 所有的选项都勾选上之后连接的设备，用&&来连接多个参数字符串
Android://127.0.0.1:5037/79d03fa?cap_method=JAVACAP&&ori_method=ADBORI&&touch_method=ADBTOUCH
```

注意：命令行中如果有出现 `^ < > | &` 这些字符，可能都需要转义才能生效。

因此如果连接字符串中需要写 `&&` 时，在windows下需要改写成 `^&^&` ，添加一个 `^` 符号进行转义，在mac下则需要添加`\`进行转义：

```
# --device Android://127.0.0.1:5037/79d03fa?cap_method=JAVACAP&&ori_method=ADBORI 在windows下不可用
--device Android://127.0.0.1:5037/79d03fa?cap_method=JAVACAP^&^&ori_method=ADBORI  # windows命令行添加^转义后效果
--device Android://127.0.0.1:5037/79d03fa?cap_method=JAVACAP\&\&ori_method=ADBORI  # mac命令行添加\转义
```

## Android接口调用

所有在`airtest.core.api`中定义的接口，都可以在Android平台上使用，直接在脚本中调用即可：

```
from airtest.core.api import *
touch((100, 200))
# 启动某个应用
start_app("org.cocos2d.blackjack")
# 传入某个按键响应
keyevent("BACK")
```

可以查阅[airtest.core.api](https://airtest.readthedocs.io/zh_CN/latest/all_module/airtest.core.api.html)文档获得API列表。


### Android设备接口

除了在airtest.core.api中提供的跨平台接口之外，Android设备对象还有很多内置的接口可以调用，我们可以在[airtest.core.android.android module](https://airtest.readthedocs.io/zh_CN/latest/all_module/airtest.core.android.android.html)这个文档中查阅到Android设备对象拥有的方法，然后像这样调用：

```
dev = device()  # 获取到当前设备的Android对象
print(dev.get_display_info())  # 查看当前设备的显示信息
print(dev.list_app())  # 打印出当前安装的app列表
```

### ADB指令调用

利用Android设备接口，我们可以这样调用adb指令：

```
# 对当前设备执行指令 adb shell ls
print(shell("ls"))

# 对特定设备执行adb指令
dev = connect_device("Android:///device1")
dev.shell("ls")

# 切换到某台设备，执行adb指令
set_current(0)
shell("ls")
```

## Android常见问题与代码示例

### Android模拟器连接

模拟器与真机的连接方式类似，需要进行以下步骤：

- 打开模拟器上的开发者选项，并勾选允许USB调试。部分模拟器可能需要找到 `设置-关于手机` 点击多次后才能打开开发者选项
- 使用adb连上对应的端口号，例如输入`adb connect 127.0.0.1:62001`，其中7555是模拟器对应的端口号，每个品牌模拟器不相同
- 可以使用代码`Android://127.0.0.1:5037/127.0.0.1:62001?cap_method=JAVACAP`连上对应的模拟器

注意要点：

- 大部分模拟器无法使用默认参数连接，必须要指定`cap_method=JAVACAP`
- 各品牌模拟器的端口可以查阅[Android模拟器连接](https://airtest.doc.io.netease.com/IDEdocs/device_connection/3_emulator_connection/#2)

### 连续滑动

我们提供了一些滑动方面的接口，方便大家进行更复杂的操作：

```
dev = device()  # 获取当前设备
dev.pinch()  # 双指捏合或分开
dev.swipe_along([(100, 300), (300, 300), (100, 500), (300, 600)])  # 连续滑过一系列坐标
dev.two_finger_swipe( (100, 100), (200, 200) )  # 两个手指一起滑动
```

其中，`swipe_along`可以连续不断地划过一系列坐标点，是最常用的一个接口。

### 自定义滑动

在`airtest.core.android.touch_methods.base_touch`中，定义了4个动作事件：

- `DownEvent(coordinates, contact=0, pressure=50)` 手指按下
- `UpEvent(contact=0)` 手指抬起
- `MoveEvent(coordinates, contact=0, pressure=50)` 滑动到某个坐标
- `SleepEvent(seconds)` 等待

上述4个动作中，`contact`参数默认为0，代表了第一根手指，如果传入1，就可以定义第二根手指的动作，这样就能实现双指的复杂操作了。

`pressure=50`定义了按下时的压力，默认为50。

例如`touch`接口，实际上是由`[DownEvent, SleepEvent, UpEvent]`三个动作组成的，理论上组合这些动作，能够自定义非常复杂的点击滑动操作。


例如这是一个双指轻点屏幕的例子：

```
from airtest.core.android.touch_methods.base_touch import *
# tap with two fingers
multitouch_event = [
    DownEvent((100, 100), 0),
    DownEvent((200, 200), 1),  # second finger
    SleepEvent(1),
    UpEvent(0), UpEvent(1)]

device().touch_proxy.perform(multitouch_event)
```

在上面的示例代码中，先在(100, 100)的坐标按下第一个手指，在(200, 200)按下第二个手指，等待一秒后再分别抬起两个手指。

还可以加入`MoveEvent`来实现更丰富的操作，例如一个普通的`swipe`是这样实现的：

```
swipe_event = [DownEvent((500, 500)), SleepEvent(0.1)]

for i in range(5):
    swipe_event.append(MoveEvent((500 + 100*i, 500 + 100*i)))
    swipe_event.append(SleepEvent(0.2))

swipe_event.append(UpEvent())

dev.touch_proxy.perform(swipe_event)
```

在此基础上进行改进，可以实现更多复杂操作，例如长按2秒-滑动到某个位置：

```
from airtest.core.android.touch_methods.base_touch import *
dev = device()

# 长按删除应用
longtouch_event = [
    DownEvent([908, 892]),  # 待删除应用的坐标
    SleepEvent(2),
    MoveEvent([165,285]),  # 删除应用的垃圾桶坐标
    UpEvent(0)]

dev.touch_proxy.perform(longtouch_event)
```

更多示例，请参考[airtest/playground/android_motionevents.py](https://github.com/AirtestProject/Airtest/blob/master/playground/android_motionevents.py)。

#### Debug tips

你可以打开`手机设置-开发者选项-显示触摸位置`来调试模拟输入的操作，这样做能看到每次点击的位置。


### 在运行脚本过程中录屏

Android手机支持在运行脚本过程中对屏幕进行录制，在运行脚本的命令行中加入`--recording`参数即可：

```
airtest run "D:\test\Airtest_example.air"  --device android:/// --log logs/ --recording
```

运行完毕后，可以在指定的log目录中找到录制完毕的mp4文件。

- 如果只传了`--recording`参数，默认将会使用`recording_手机序列号.mp4`来命名录屏文件
- 如果指定了文件名`--recording test.mp4`，且超过一台手机，就命名为 `手机序列号_test.mp4`
- 如果指定了文件名`--recording test.mp4`，且只有一台手机，就命名为 `test.mp4`
- **注意传入的文件名必须以mp4作为结尾**
- 默认录屏文件最长为1800秒，如果需要录制更长时间，需要手动在代码中调用录屏接口

如果在代码中调用录屏接口，能够控制录屏时的清晰度和时长，文档参见[Android.start_recording](../../all_module/airtest.core.android.android.html#airtest.core.android.android.Android.start_recording)。

例如，以最低清晰度录制一段30秒的视频，并导出到当前目录下的`test.mp4`：

```python
from airtest.core.api import connect_device, sleep
dev = connect_device("Android:///")
# Record the screen with the lowest quality
dev.start_recording(bit_rate_level=1)
sleep(30)
dev.stop_recording(output="test.mp4")
```

`bit_rate_level`用于控制录屏的清晰度，取值范围是1-5，`bit_rate_level=5`清晰度最高，但是占用的硬盘空间也会更大。

或者设置参数`max_time=30`，30秒后将自动停止录屏：

```python
dev = device()
dev.start_recording(max_time=30, bit_rate_level=5)
dev.stop_recording(output="test_30s.mp4")
```

`max_time`默认值为1800秒，所以录屏最大时长是半小时，可以修改它的值以获得更长时间的录屏：

```python
dev = device()
dev.start_recording(max_time=3600, bit_rate_level=5)
dev.stop_recording(output="test_hour.mp4")
```

## 更多参考教程和文档

- [如何在Android手机上进行自动化测试](https://airtest.doc.io.netease.com/tutorial/4_Android_automated_testing_one/)
- [Android连接常见问题](https://airtest.doc.io.netease.com/IDEdocs/device_connection/2_android_faq/)
