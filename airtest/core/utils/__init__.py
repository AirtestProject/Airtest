from airtest.core.utils.cleanup import reg_cleanup
from airtest.core.utils.logger import get_logger
from airtest.core.utils.logwraper import AirtestLogger, Logwrap
from airtest.core.utils.nbsp import NonBlockingStreamReader
from airtest.core.utils.retry import retries
from airtest.core.utils.safesocket import SafeSocket
from airtest.core.utils.transform import TargetPos
from airtest.core.utils.snippet import split_cmd, get_std_encoding
from airtest.core.utils.resolution import cocos_min_strategy, predict_area