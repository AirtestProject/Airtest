# encoding=utf-8

"""settings can be changed by user."""

DEBUG = False
ADDRESS = ('127.0.0.1', 5037)
LOGFILE = "log.txt"
SCREEN_DIR = "img_record"
BASE_DIR = '.'
SAVE_SCREEN = None
# REFRESH_SCREEN_DELAY = 5 # to be deleted # 设备发生屏幕旋转时，需要等待5s左右才能确定旋转完毕(大部分设备)
# RECONNECT_TIMES = 5 # to be deleted
RESIZE_METHOD = None
SCRIPTHOME = None
SRC_RESOLUTION = []  # to be move to DEVICE
CVSTRATEGY = None
CVSTRATEGY_ANDROID = ["siftpre", "siftnopre", "tpl"]
CVSTRATEGY_WINDOWS = ["tpl", "siftnopre"]
FIND_INSIDE = None
FIND_OUTSIDE = None
WHOLE_SCREEN = False  # 指定WHOLE_SCREEN时，就默认截取全屏(而非hwnd窗口截图)
CHECK_COLOR = False
# MASK_RECT = None  # windows模式下IDE运行时，屏蔽掉IDE区域(MASK_RECT)
THRESHOLD = 0.6
THRESHOLD_STRICT = 0.7
STRICT_RET = True
CVINTERVAL = 0.5
# PLAYRES = [] # to be deleted
OPDELAY = 0.1
TIMEOUT = 20
WINDOW_TITLE = None

FIND_TIMEOUT = 20
FIND_TIMEOUT_TMP = 3
