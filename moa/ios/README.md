# Moa-ios分支
***

## 文件说明

### 1. client.py

定义了moa－ios客户端及其相关方法，包括应用的安装，卸载，启动，停止，设备截图，以及获取设备的朝向和分辨率等。

### 2. utils.py

操控ios设备的底层工具包，主要都是通过imobiledevice库完成，少数几个需要直接使用idevice系统的命令行工具实现。

### 3. resign.py & floatsign.sh

重签脚本。resign.py脚本中设置一些基本变量，然后调用floatsign.sh脚本对ipa进行重签。

floatsign.sh的git库：[https://github.com/nanonation/floatsign/](https://github.com/nanonation/floatsign/)

### 4. resign-directory

resign目录中存放了重签所需的provision和entitlements文件。


### 5. DeviceSupport-directory 

DeviceSupport目录存放了在使用imobiledevice库启动ios设备上的app时需要先在设备上挂载的DeveloperDiskImage。

这些文件可以在安装了Xcode的Mac上找到，对应的目录是

```
/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/DeviceSupport
```
