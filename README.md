## moa
## Developing

该项目起源于[airtest](https://github.com/netease/airtest), 是一个通过图像识别技术，自动化测试App的技术


## 接口说明

### set\_address((host, port))

	设置adb的host和port，默认取本地adb

### set\_serialno(sn=None)

	设置手机的序列号, 支持*匹配。如果adb连接了多台手机，默认取第一台

		set_serialno('cff*')

### connect(url)

	使用了这个函数，就可以省去设置set_address和set_serialno了.

		connect('moa://127.0.0.1:5037/cffab*')

### set\_basedir(base\_dir)

	设置你的工作目录，日志，图片都会以这个基准去查找

### set\_logfile(filename, inbase=True)

	设置日志文件的路径，如果inbase为true的话，日志会保存到basedir目录下

### ~~gevent_run(func)~~

	~~用于windows或mac上的调试功能~~

### log(tag, data)

	data一定是需要json.dumps支持的格式才行.

### shell(cmd, shell=True)

	执行shell命令，然后返回

		print shell('echo hello')
		# output: hello

### amstart(package)

	am: android manager的简称

		amstart('com.netease.moa') # 启动应用

### amstop(package)

	强制停止应用，等同于`am force-stop <package>`

### amclear(package)

	清空应用中的数据，等同于`pm clear <package>`

### snapshot(filename="screen.png")

	保存手机上的截图到filename这个文件。然后返回图像的二进制内容

### wake()

	点亮手机屏幕

### home()

	点击手机home键

### touch(v, timeout=TIMEOUT, delay=OPDELAY, offset=None)

	点击屏幕中的目标，参数如下：

		v 目标，有三种形态：坐标、图片、文字，详见MoaTarget

		timeout 超时时间

		delay 操作后延迟时间

		offset 点击坐标偏移，可以是坐标或者是屏幕百分比。offset={"percent": True, "x": 20, "y": 20}

### swipe(v1, v2=None, vector=None)

	滑动操作，两种形态：

		swipe(v1, v2) 从起点目标滑动到终点目标

		swipe(v1, vector=(x, y)) 从起点目标滑动一个向量。vector=(dx/w, dy/h)

### operate(v, route, timeout=TIMEOUT, delay=OPDELAY)

	长操作，在起点处按下，按照一个线路滑动，最终松开

		v 起点目标

		route 滑动线路 [vector1, vector2, vector3...] vector与swipe参数相同
		
		timeout 同上
		
		delay 同上

### keyevent(keyname)
	
	安卓按键

		keyname 参考：http://developer.android.com/reference/android/view/KeyEvent.html

### text(text)
	
	文字输入

### sleep(secs=1.0)

	等待时间

### wait(v, timeout=10, safe=False, interval=CVINTERVAL, intervalfunc=None)

	等待目标出现

		v 目标

		timeout 超时时间

		safe 超时是否继续，默认为False即会报错

		interval 等待目标的间隔时间

		intervalfunc 等待目标的间隔中的回调函数

### exists(v, timeout=1)

	判断目标是否存在，返回True/False

### assert_exists(v, msg="", timeout=TIMEOUT)
	
	断言目标存在，如果超时时间内不存在则抛出AssertionError

		v 目标

		msg 断言信息

		timeout 超时时间

### assert_not_exists(v, msg="", timeout=2)

	断言目标不存在，如果超时时间内存在则抛出AssertionError，参数同上

### assert_equal(first, second, msg="")
	
	断言first和second相等，不等则抛出AssertionError



### MoaPic(filename, rect=None, threshold=THRESHOLD, target_pos=TargetPos.MID, record_pos=None, resolution=[])
	
	一个隐藏的类，所有图片目标在moa中都会转换为MoaPic实例，参数如下：
		filename	图片名
		rect		所在区域(x0, y0, x1, y1)，默认全屏，不建议给这个参数
		threshold	识别阈值，默认阈值为0.6，较低，可以按需修改
		target_pos	目标图片的点击位置，默认点击目标中点，可以填1-9表示不同位置，小键盘排布
		record_pos	记录下的录制坐标，用于辅助图像识别
		resolution	记录下的屏幕分辨率，用于辅助图像识别