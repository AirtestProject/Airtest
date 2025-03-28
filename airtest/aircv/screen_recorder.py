# coding=utf-8
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import cv2
import ffmpeg
from collections import deque
import threading
import time
import numpy as np
import subprocess
import traceback
from airtest.utils.logger import get_logger
LOGGING = get_logger(__name__)


RECORDER_ORI = {
    "PORTRAIT": 1,
    "LANDSCAPE": 2,
    "ROTATION": 0,  # The screen is centered in a square
}

def resize_by_max(img, max_size=800):
    if img is None:
        return np.zeros((max_size, max_size, 3), dtype=np.uint8)
    max_len = max(img.shape[0], img.shape[1])
    if max_len > max_size:
        scale = max_size / max_len
        img = cv2.resize(img, (int(img.shape[1] * scale), int(img.shape[0] * scale)))
    return img


def get_max_size(max_size):
    try:
        max_size = int(max_size)
    except:
        max_size = None
    else:
        if max_size <= 0:
            max_size = None
    return max_size


class FfmpegVidWriter:
    """
    Generate a video using FFMPEG.
    """
    def __init__(self, outfile, width, height, fps=10, orientation=0, timetag=True):
        self.fps = fps

        # 三种横竖屏录屏模式 1 竖屏 2 横屏 0 方形居中
        self.orientation = RECORDER_ORI.get(str(orientation).upper(), orientation)
        if self.orientation == 1:
            self.height = max(width, height)
            self.width = min(width, height)
        elif self.orientation == 2:
            self.width = max(width, height)
            self.height = min(width, height)
        else:
            self.width = self.height = max(width, height)

        # 满足视频宽高条件
        self.height = height = self.height - (self.height % 32) + 32
        self.width = width = self.width - (self.width % 32) + 32
        self.cache_frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 添加时间戳
        self.timetag = timetag
        if self.timetag:
            scale = self.height*0.001
            self.tag_scale = max(0.5, min(scale, 1.5))
            thickness = int(self.height*0.002)
            # 指定时间戳的位置和粗细
            self.tag_thickness = max(1, min(thickness+1, 4))
            self.tag_pos = (0, int(self.height*0.035))

            # 生成时区信息(UTC+08:00)
            timezone_offset = time.timezone / 3600
            timezone_offset_hours = int(abs(timezone_offset))
            self.timezone_str = f"(UTC{'+' if timezone_offset <= 0 else '-'}{timezone_offset_hours:02d}:00)"

        try:
            subprocess.Popen("ffmpeg", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).wait()
        except FileNotFoundError:
            from airtest.utils.ffmpeg import ffmpeg_setter
            try:
                ffmpeg_setter.add_paths()
            except Exception as e:
                LOGGING.error("Error: setting ffmpeg path failed, please download it at https://ffmpeg.org/download.html then add ffmpeg path to PATH")
                raise

        self.process = (
            ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='rgb24',
                s='{}x{}'.format(width, height), framerate=self.fps)
            .output(outfile, pix_fmt='yuv420p', vcodec='libx264', crf=25, threads=1,
                    preset="veryfast", framerate=self.fps)
            .global_args("-loglevel", "error")
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )
        self.writer = self.process.stdin

    def process_frame(self, frame):
        assert len(frame.shape) == 3
        frame = frame[..., ::-1]
        if self.orientation == 1 and frame.shape[1] > frame.shape[0]:
            frame = cv2.resize(frame, (self.width, int(self.width*self.width/self.height)))
        elif self.orientation == 2 and frame.shape[1] < frame.shape[0]:
            frame = cv2.resize(frame, (int(self.height*self.height/self.width), self.height))
        h_st = max(self.cache_frame.shape[0]//2 - frame.shape[0]//2, 0)
        w_st = max(self.cache_frame.shape[1]//2 - frame.shape[1]//2, 0)
        h_ed = min(h_st+frame.shape[0], self.cache_frame.shape[0])
        w_ed = min(w_st+frame.shape[1], self.cache_frame.shape[1])
        self.cache_frame[:] = 0
        self.cache_frame[h_st:h_ed, w_st:w_ed, :] = frame[:(h_ed-h_st), :(w_ed-w_st)]
        if self.timetag:
            cv2.putText(self.cache_frame, time.strftime("%Y-%m-%d %H:%M:%S" + self.timezone_str),
                        self.tag_pos, cv2.FONT_HERSHEY_SIMPLEX, self.tag_scale,
                        (0, 255, 0), self.tag_thickness)
        return self.cache_frame.copy()

    def write(self, frame):
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)
        self.writer.write(frame)

    def close(self):
        try:
            self.writer.close()
            self.process.wait(timeout=5)
        except Exception as e:
            LOGGING.error(f"Error closing ffmpeg process: {e}", exc_info=True)
        finally:
            try:
                self.process.terminate()
            except Exception as e:
                LOGGING.error(f"Error terminating ffmpeg process: {e}", exc_info=True)


class ScreenRecorder:
    def __init__(self, outfile, get_frame_func, fps=10, snapshot_sleep=0.001, orientation=0, timetag=True):
        self.get_frame_func = get_frame_func
        self.tmp_frame = self.get_frame_func()
        self.snapshot_sleep = snapshot_sleep

        width, height = self.tmp_frame.shape[1], self.tmp_frame.shape[0]
        self.writer = FfmpegVidWriter(outfile, width, height, fps, orientation, timetag)
        self.tmp_frame = self.writer.process_frame(self.tmp_frame)
        self.frame_queue = deque(maxlen=100)
        self.frame_queue.append((time.time(), self.tmp_frame))

        self._is_running = False
        self._stop_flag = False
        self._stop_time = 0

    def is_running(self):
        return self._is_running

    @property
    def stop_time(self):
        return self._stop_time

    @stop_time.setter
    def stop_time(self, max_time):
        if isinstance(max_time, int) and max_time > 0:
            self._stop_time = time.time() + max_time
        else:
            LOGGING.error("failed to set stop time")

    def is_stop(self):
        if self._stop_flag:
            return True
        if self._stop_time > 0 and time.time() >= self._stop_time:
            return True
        return False

    def start(self):
        if self._is_running:
            LOGGING.warning("recording is already running, please don't call again")
            return False
        self._is_running = True
        self.t_stream = threading.Thread(target=self.get_frame_loop)
        self.t_stream.setDaemon(True)
        self.t_stream.start()
        self.t_write = threading.Thread(target=self.write_frame_loop)
        self.t_write.setDaemon(True)
        self.t_write.start()
        return True

    def stop(self):
        self._is_running = False
        self._stop_flag = True
        if hasattr(self, 't_write') and self.t_write.is_alive():
            self.t_write.join()
        if hasattr(self, 't_stream') and self.t_stream.is_alive():
            self.t_stream.join()
        if self.writer:
            self.writer.close()  # Ensure writer is closed

    def get_frame_loop(self):
        # 单独一个线程持续截图
        try:
            while True:
                try:
                    tmp_frame = self.get_frame_func()
                except Exception as e:
                    LOGGING.error(f"Error getting frame: {e}", exc_info=True)
                    tmp_frame = None
                
                if tmp_frame is None:
                    # 获取帧失败，生成一张包含错误信息的空白图片
                    LOGGING.warning("get frame error, use blank frame")
                    tmp_frame = np.zeros_like(self.tmp_frame)
                    cv2.putText(tmp_frame, '[warning] get frame error', 
                            (int(self.writer.width*0.1), int(self.writer.height*0.5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)
                    time.sleep(1)

                self.tmp_frame = self.writer.process_frame(tmp_frame)
                self.frame_queue.append((time.time(), self.tmp_frame))
                time.sleep(0.5/self.writer.fps)
                if self.is_stop():
                    break
            self._stop_flag = True
        except Exception as e:
            LOGGING.error("record thread error", exc_info=True)
            self._stop_flag = True
            raise

    def write_frame_loop(self):
        try:
            duration = 1.0/self.writer.fps
            step = 0
            start_time = None
            last_frame = None
            self._stop_flag = False
            while True:
                if self.writer.process.poll() is not None:  # 检查 FFmpeg 进程状态
                    LOGGING.error("FFmpeg process has terminated unexpectedly. Exiting write loop.")
                    break
                if len(self.frame_queue) > 0:
                    t, frame = self.frame_queue.popleft()
                    if last_frame is None:
                        try:
                            self.writer.write(frame)
                        except BrokenPipeError:
                            LOGGING.error("Broken pipe error while writing frame. Terminating write loop.")
                            break
                        last_frame = frame
                        start_time = t
                    else:
                        while start_time + step * duration < t:
                            step += 1
                            try:
                                self.writer.write(last_frame)
                            except BrokenPipeError:
                                LOGGING.error("Broken pipe error while writing frame. Terminating write loop.")
                                break
                        last_frame = frame
                else:
                    time.sleep(0.1)
                    # 如果没有新的帧，且已经停止，则退出
                    if self.is_stop():
                        break
            self.writer.close()
            self._stop_flag = True
        except Exception as e:
            LOGGING.error("write thread error", exc_info=True)
            self._stop_flag = True
            self.writer.close()  # Ensure the writer is closed on error
            raise
