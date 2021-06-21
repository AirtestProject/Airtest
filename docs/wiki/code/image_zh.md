# 图像相关的问题


## 如何修改Airtest的图像识别算法
Airtest的全局设置中，`CVSTRATEGY` 用于设置Airtest的图像识别算法，默认情况下 `CVSTRATEGY = ["surf", "tpl", "brisk"]` ，每次查找图片的时候，airtest就会按照这个设置好的算法顺序去执行，直到找出一个符合设定阈值的识别结果，或者是一直按照这个算法顺序循环查找，直到超时。

我们可以自定义Airtest的图像识别算法，示例如下：

```
from airtest.core.settings import Settings as ST

ST.CVSTRATEGY = ["tpl", "sift","brisk"]
```
### 如何判断截图是否存在

检查当前设备画面上是否存在目标截图，常和判断语句一起使用，示例：

```
if exists(Template(r"tpl1606822430589.png", record_pos=(-0.006, 0.069), resolution=(1080, 1920)))
    touch(Template(r"tpl1606822430589.png", record_pos=(-0.006, 0.073), resolution=(1080, 1920)))  
```

### 如何等待某个截图目标出现
等待当前画面上出现某个匹配的 `Template` 图片，常用于等待某一张图片出来之后，再进行下一步操作，可以传入等待的超时时长、查找的时间间隔和首次尝试查找失败的回调函数，示例：

```
def test():
    print("未等待到目标")

wait(Template(r"tpl1606821804906.png", record_pos=(-0.036, -0.189), resolution=(1080, 1920)),timeout=120,interval=3,intervalfunc=test) 
```

## 如何设置图像查询的超时时长
在进行图像匹配时，会循环用几个算法去识别，但是循环识别并不是无限的，这里有一个查询的超时时长设置，一旦查询时间大于超时时长，还是未找到可信度大于阙值的结果，那就认定此次匹配失败，默认的超时时长如下：

```
FIND_TIMEOUT = 20
FIND_TIMEOUT_TMP = 3
```

使用 `FIND_TIMEOUT` 作为超时时长的接口有很多，比如：`assert_exists()`、`touch()`、`wait()`、`swipe()` 等。

而使用 `FIND_TIMEOUT_TMP` 作为超时时长的接口则比较少，比如：`assert_not_exists()`、`exists()` 等。

与阙值类似，我们既可以修改全局的超时时长，也可以设置单条语句的超时时长，示例如下：

```
from airtest.core.settings import Settings as ST

# 设置全局的超时时长为60s
ST.FIND_TIMEOUT = 60
ST.FIND_TIMEOUT_TMP = 60

# 设置单条wait语句的超时时长
wait(Template(r"tpl1607425650104.png", record_pos=(-0.044, -0.177), resolution=(1080, 1920)),timeout=120)
```

### 16.如何修改图像的阙值
`THRESHOLD` 和 `THRESHOLD_STRICT` 都是图像识别的阙值，Airtest1.1.6版本之后，所有用到了图像识别的接口，都是用 `THRESHOLD` 作为阙值。它的默认值为0.7，取值范围[0,1]。

在进行图像匹配时，只有当识别结果的可信度大于阙值时，才认为找到了匹配的结果。

除了可以修改全局的图像识别阙值，我们还支持修改单张图片的阙值，需要注意的是，如我们没有单独设置图像的阙值，将默认使用全局阙值 `THRESHOLD` ，示例如下：

```
from airtest.core.settings import Settings as ST

# 设置全局阙值为0.8
ST.THRESHOLD = 0.8

# 设置单张图片的阙值为0.9
touch(Template(r"tpl1607424190850.png", threshold=0.9, record_pos=(-0.394, -0.176), resolution=(1080, 1920)))
```

在Airtest1.1.6之前， `assert_exists` 使用的图像阙值 是 `THRESHOLD_STRICT` 。所以使用1.1.6之前版本的同学，想要修改 `assert_exists` 的图像阙值，需要设置  `THRESHOLD_STRICT` 的值。
