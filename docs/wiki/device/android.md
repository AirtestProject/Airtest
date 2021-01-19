# Android device connection methods and FAQs

[中文版](android_zh.md)

## Android phone connection

If use AirtestIDE to mobile phone connection, please refer to the [documents](https://airtest.doc.io.netease.com/en/IDEdocs/device_connection/1_android_phone_connection/)

If you're not going to use AirtestIDE, have a look at this statement:

- Opens the **developer options** on the phone, and **allows USB debugging** 
- After using USB to connect the phone, you can see the device using `adb devices` command and refer to [Use ADB to see if the phone is successfully connected](#use-adb-to-see-if-the-phone-is-successfully-connected) 
- On the code and command line, connect the phone with the phone`s serial number, see [Use the phone in your code](#use-the-phone-in-your-code) 


### Use ADB to see if the phone is successfully connected 

`adb` is the official Android command line tool for Google, which allows us to communicate with devices.(if you are interested, please refer to: [adb](https://developer.android.com/studio/command-line/adb).)

We have stored `adb` executables for each platform under `airtest\airtest\core\Android\static\adb` directory, you can use it without downloading.

Take Windows as an example, you can first use the terminal to enter the directory where `adb.exe` is located (in `airtest\airtest\core\Android\static\adb\Windows`, `shift+right click` to open the command line terminal), and then execute the command line of `adb devices` :

```
E:\airtest\airtest\core\android\static\adb\windows>adb devices

List of devices attached
c2b1c2a7        device
eba17551        device
127.0.0.1:10033 device
```

In MAC, you can visit `airtest/core/android/static/adb/mac` directory and run the `./adb devices`, if the adb no executable permissions, can run `chmod + x adb` add executable permissions for it.

- In the above example, you can see that the 3 Android devices currently connected, whose state is `device`, are normally online 
- If the device status is `UNAUTHORIZED`, click OK in the `ALLOW USB Debugging` menu that pops up over the phone 
- If you can't see the device name, you may need to install the phone's official driver on your PC 

### If your phone has a connection problem

Due to different mobile phone manufacturers and the corresponding model, may encounter all sorts of problems in the process of connecting, please refer to the link common problems [Android](https://airtest.doc.io.netease.com/en/IDEdocs/device_connection/2_android_faq/)

### Use the phone in your code 

After confirming that the phone can be successfully connected, we can see the device serial number of the phone in the command line of `adb devices` :

```
> adb devices 

List of devices attached
c2b1c2a7        device
```

The `c2B1c2A7` above is the device serial number of the mobile phone. We define a mobile phone with the following format string:

```
Android://<adbhost>:<adbport>/<serialno>
```

Among them:

- `adbhost` is the IP of the host where adb Server is located. By default, this is `localhost`or `127.0.0.1`
- `adb port` defaults to 5037
- `serialno` is the serial number of the Android phone, such as `c2B1c2a7` just now

Here are some examples:

```
# Will default to the first phone in the current connection if you fill in nothing 
Android:///
# A phone with c2B1C2a7 connected to the default port of the native 
Android://127.0.0.1:5037/c2b1c2a7
# Connect a remote device through ADB connect with the native ADB. Note that 10.254.60.1:5555 is actually Serialno 
Android://127.0.0.1:5037/10.254.60.1:5555
```

#### Connect the phone according to the `Android:///` string 

When we run a script from the command line, we can use `--device Android:///` to specify the Android device on which the script will run, for example:

```
>airtest run untitled.air --device Android:/// phone serial number --log log/
```

In addition, we can use the `connect_device` interface when we want to connect the phone in our code:

```
from airtest.core.api import *
connect_device("Android:///Phone Serial Number")
```

These two methods only need to choose one of them, basically can meet our needs to connect devices.


#### Some special parameters 

Some special devices may appear black screen when connected, such as some emulators, we can add an extra parameter `cap_method=JAVACAP` to force the screen capture mode to be `JAVACAP` :

```
# Connect the emulator and check the `Use Javacap` mode 
Android://127.0.0.1:5037/127.0.0.1:7555?cap_method=JAVACAP
```

In addition, we have two other parameters, `ori_method=ADBORI`, which specifies the rotation mode of the device screen, and `touch_method=ADBTOUCH`, which specifies the click mode of the screen as ADB instruction.

For the most part, we don't need to specify these parameters, and we only need to add additional parameters if some special Android devices (such as some special models of tablets) can`t connect with the default parameters:

```
# Check all the options to connect the device and use && to connect multiple parameter strings 
Android://127.0.0.1:5037/79d03fa?cap_method=JAVACAP&&ori_method=ADBORI&&touch_method=ADBTOUCH
```

Note: if any of the characters `^<>|&`appear on the command line, they may need to be escaped to take effect.

Therefore, if you need to write `&&` in the connection string, you need to rewrite it as `^&^&` in Windows, add a `^` symbol for escape, and add `\` for escape under MAC:

```
# -- device Android://127.0.0.1:5037/79d03fa?cap_method=JAVACAP&&ori_method=ADBORI is not available under Windows 
--device Android://127.0.0.1:5037/79d03fa?cap_method=JAVACAP^&^&ori_method=ADBORI # Windows command line add ^ escape effect
--device Android://127.0.0.1:5037/79d03fa?cap_method=JAVACAP\&\&ori_method=ADBORI # MAC command line add \ escape
```

## Android interface calls

All interfaces defined in `airtest.core.api` can be used on the Android platform and can be called directly in the script:

```
from airtest.core.api import *
touch((100, 200))
# Start an application 
start_app("org.cocos2d.blackjack")
# Pass in a key response 
keyevent("BACK")
```

Can refer to [airtest.core.api](https://airtest.readthedocs.io/zh_CN/latest/all_module/airtest.core.api.html) for the API list.


### Android device interface

In addition to the cross-platform interface provided in `airtest.core.api`, Android device objects have many built-in interfaces that can be called,We can [airtest core. Android. Android module](https://airtest.readthedocs.io/zh_CN/latest/all_module/airtest.core.android.android.html) in this document refer to the android device object has a method, and then call something like this:

```
dev = device() # gets the Android object to the current device
print(dev.get_display_info()) # to view the display information for the current device
print(dev.list_app()) # prints out the list of currently installed apps
```

### The ADB instruction call

Using the Android device interface, we can call adb directives like this:

```
# Execute the instruction ADB shell LS on the current device 
print(shell("ls"))

# Execute the ADB instruction for a specific device 
dev = connect_device("Android:///device1")
dev.shell("ls")

# Switch to a device and execute adb instruction 
set_current(0)
shell("ls")
```

## Frequently asked Questions about Android

### Android emulator connection

The simulator is connected in a similar way to the real machine. The following steps are required:

- Open developer options on the emulator and check to allow USB debugging. Some emulators may need to find `Settings - about the phone` multiple times before opening the developer options
- Use ADB to connect the corresponding port number, for example, enter `adb connect 127.0.0.1:62001`, where 7555 is the port number corresponding to the simulator, and each brand simulator is different 
- you can use the code `Android://127.0.0.1:5037/127.0.0.1:62001?cap_method=JAVACAP` connects to the corresponding emulator

Key points to note:

- Most emulators cannot connect with default parameters and must specify `cap_method=JAVACAP` 
- each brand simulator port can be refer to [Android emulator](https://airtest.doc.io.netease.com/en/IDEdocs/device_connection/3_emulator_connection/#2) 

### Slide continuously 

We provide some sliding interfaces to facilitate more complex operations:

```
dev = device()  # gets the current device
dev.pinch()  # Two fingers pinch or separate
dev.swipe_along([(100, 300), (300, 300), (100, 500), (300, 600)]) # continuously slides over a series of coordinates
dev.two_finger_swipe((100, 100), (200, 200))  # both fingers slip together
```

Among them, `swipe_along` can continuously streak through a series of coordinate points, which is the most commonly used interface.

### Custom slide 

In `airtest.core.android.touch_methods.base_touch`, defines four action events:

- `DownEvent(Coordinates, contact=0, pressure=50)` click
- `UpEvent(contact=0)` finger up
- `MoveEvent(coordinates, contact=0, pressure=50)` slide to a coordinate
- `SleepEvent` wait (seconds)

In the above four actions, the `contact` parameter defaults to 0, representing the first finger. If 1 is passed in, the action of the second finger can be defined, so that the complex operation of the double-finger can be achieved.

`pressure=50` defines the pressure when pressed and defaults to 50.

The `touch` interface, for example, is actually made up of `[DownEvent, SleepEvent, UpEvent]` actions, which in theory can be combined to allow you to customize very complex click-and-slide operations.


For example, here`s an example of a two-fingered tap on a screen:

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

In the example code above, press the first finger at the coordinates of (100, 100), press the second finger at (200, 200), and wait for a second before lifting each finger.

Also, `MoveEvent` can be added to achieve more diversified operations, such as an ordinary `swipe` :

```
Swipe_event = [DownEvent((500, 500)), SleepEvent(0.1)]

for i in range(5):
     swipe_event.append(MoveEvent((500 + 100*i, 500 + 100*i)))
     Swipe_event. Append (SleepEvent (0.2))

swipe_event.append(UpEvent())

dev.touch_proxy.perform(swipe_event)
```

Based on this improvement, more complex operations can be achieved, such as long press 2 seconds - slide to a position:

```
from airtest.core.android.touch_methods.base_touch import *
dev = device()

# Long press delete application 
longtouch_event = [
     DownEvent([908, 892]),  # coordinates of the application to be deleted
     SleepEvent(2),
     MoveEvent([165,285]),  # delete the application's garbage can coordinates
     UpEvent(0)]

dev.touch_proxy.perform(longtouch_event)
```

More examples, please refer to the [airtest/playground/android_motionevents.py](https://github.com/AirtestProject/Airtest/blob/master/playground/android_motionevents.py).

#### Debug tips

You can switch on `settings-developer options-show input position` on your phone to debug simulated inputs.

### Record the screen while running the script 

Android phones support recording the screen while running the script. Add the `--recording` parameter to the command line of running the script:

```
airtest run "D:\test\Airtest_example.air"  --device android:/// --log logs/ --recording
```

After running, you can find the mp4 file recorded in the specified log directory.

- If only the `--recording` parameter has been passed, by default `recording_serialnumber.mp4` will be used to name the recording screen file 
- If the file name `--recording test.mp4` is specified and there is more than one phone, name it `serialnumber.mp4` 
- If you specify the filename `--recording test.mp4` and have only one phone, call it `test.mp4` 
- **Note that the file name passed in must end with mp4**
- The default screen recording file is up to 1800 seconds. If you need to record for a longer time, you need to manually call the screen recording interface in the code

If you call the screen recording interface in the code, you can control the clarity and duration of the screen recording. For the document, see [Android.start_recording](../../all_module/airtest.core.android.android.html#airtest.core.android.android.Android.start_recording).

For example, to record a 30-second video with the lowest definition and export it to `test.mp4` in the current directory:

```python
from airtest.core.api import connect_device, sleep
dev = connect_device("Android:///")
# Record the screen with the lowest quality
dev.start_recording(bit_rate_level=1)
sleep(30)
dev.stop_recording(output="test.mp4")
```

`bit_rate_level` is used to control the resolution of screen recording. The value range is 1-5. `bit_rate_level=5` has the highest resolution, but it will take up more hard disk space.

Or set the parameter `max_time=30`, the screen recording will automatically stop after 30 seconds:

```python
dev = device()
dev.start_recording(max_time=30, bit_rate_level=5)
dev.stop_recording(output="test_30s.mp4")
```

The default value of `max_time` is 1800 seconds, so the maximum screen recording time is half an hour, you can modify its value to get a longer screen recording:

```python
dev = device()
dev.start_recording(max_time=3600, bit_rate_level=5)
dev.stop_recording(output="test_hour.mp4")
```

## Refer to the tutorial and documentation for more 

- [Automated Testing on Android Phones-part 1](https://airtest.doc.io.netease.com/en/tutorial/4_Android_automated_testing_one/)
- [Android connection FAQ](https://airtest.doc.io.netease.com/en/IDEdocs/device_connection/2_android_faq/)
