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

***

## 依赖说明

### 依赖库安装

ios设备的控制需要依赖libimobiledevice库，这个库有两种安装办法

1. 在Mac系统下，这个库的安装可以直接通过homebrew进行，它会自动解决相应的依赖关系。

	```
	$ brew install libimobiledevice
	```


2. 但是，为了使用其对应的python库，甚至对源码做一些修改以适应我们的需求，则最好使用源码编译的方法进行安装。

	需要安装的库有libplist和libimobiledevice，它们的github地址分别是
[libimobiledevice](https://github.com/libimobiledevice/libimobiledevice.git)
[libplist](https://github.com/libimobiledevice/libplist.git)

	安装方法都是在clone后的目录下面执行

	```
	./autogen.sh
	make
	sudo make install
	```

	正常情况下，在执行./autogen.sh之后，能够看到

	```
	...
	build_cython......:yes
	...
	```

	此时表明，继续执行命令make会对cython子目录进行编译，进而获得相应的python库。
	
### 源码修改

在使用这个库的时候，对源码考虑进行两处修改

1. 修改位置在

	```
	libimobiledevice/src/installation_proxy.c#L473
	```

	在这一行之前添加

	```
	if (status_cb == NULL)        async = INSTPROXY_COMMAND_TYPE_SYNC;
	```

	其作用是保证使用imobiledevice库进行app安装时使用的是同步运行方案。

2. 修改位置在

	```
	libimobiledevice/cython/sbservices.pxi
	```

	修改内容有
	- 代码开头添加枚举定义
	
	```
	ctypedef enum sbservices_interface_orientation_t:        SBSERVICES_INTERFACE_ORIENTATION_UNKNOWN                = 0        SBSERVICES_INTERFACE_ORIENTATION_PORTRAIT               = 1        SBSERVICES_INTERFACE_ORIENTATION_PORTRAIT_UPSIDE_DOWN   = 2        SBSERVICES_INTERFACE_ORIENTATION_LANDSCAPE_RIGHT        = 3        SBSERVICES_INTERFACE_ORIENTATION_LANDSCAPE_LEFT         = 4
	```
	
	- 添加引用函数说明
	
	```
	sbservices_error_t sbservices_get_interface_orientation(sbservices_client_t client, sbservices_interface_orientation_t* interface_orientation);
	```
	
	- 添加函数定义
	
	```
	cpdef int get_orientation(self):        cdef:            sbservices_interface_orientation_t interface_orientation            sbservices_error_t err        err = sbservices_get_interface_orientation(self._c_client, &interface_orientation)        try:            self.handle_error(err)        except BaseError, e:            raise        else:            return interface_orientation
	```
	
	修改后的效果时，可以使用SpringboardServicesClient的get_orientation函数获取屏幕的朝向
	
修改代码之后重新进行编译安装即可生效。