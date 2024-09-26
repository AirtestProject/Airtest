# coding=utf-8
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import cv2
import ffmpeg
import threading
import time
import numpy as np
import subprocess
import traceback


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
    def __init__(self, outfile, width, height, fps=10, orientation=0):
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

        try:
            subprocess.Popen("ffmpeg", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).wait()
        except FileNotFoundError:
            from airtest.utils.ffmpeg import ffmpeg_setter
            try:
                ffmpeg_setter.add_paths()
            except Exception as e:
                print("Error: setting ffmpeg path failed, please download it at https://ffmpeg.org/download.html then add ffmpeg path to PATH")
                raise

        self.process = (
            ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='rgb24',
                s='{}x{}'.format(width, height), framerate=self.fps)
            .output(outfile, pix_fmt='yuv420p', vcodec='libx264', crf=25,
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
        return self.cache_frame.copy()

    def write(self, frame):
        self.writer.write(frame.astype(np.uint8))

    def close(self):
        try:
            self.writer.close()
            self.process.wait(timeout=5)
        except Exception as e:
            print(f"Error closing ffmpeg process: {e}")
        finally:
            try:
                self.process.terminate()
            except Exception as e:
                print(f"Error terminating ffmpeg process: {e}")


class ScreenRecorder:
    def __init__(self, outfile, get_frame_func, fps=10, snapshot_sleep=0.001, orientation=0):
        self.get_frame_func = get_frame_func
        self.tmp_frame = self.get_frame_func()
        self.snapshot_sleep = snapshot_sleep

        width, height = self.tmp_frame.shape[1], self.tmp_frame.shape[0]
        self.writer = FfmpegVidWriter(outfile, width, height, fps, orientation)
        self.tmp_frame = self.writer.process_frame(self.tmp_frame)

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
            print("failed to set stop time")

    def is_stop(self):
        if self._stop_flag:
            return True
        if self._stop_time > 0 and time.time() >= self._stop_time:
            return True
        return False

    def start(self):
        if self._is_running:
            print("recording is already running, please don't call again")
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
        self.t_write.join()
        self.t_stream.join()
        self.writer.close()  # Ensure writer is closed

    def get_frame_loop(self):
        # 单独一个线程持续截图
        try:
            while True:
                tmp_frame = self.get_frame_func()
                self.tmp_frame = self.writer.process_frame(tmp_frame)
                time.sleep(self.snapshot_sleep)
                if self.is_stop():
                    break
            self._stop_flag = True
        except Exception as e:
            print("record thread error", e)
            self._stop_flag = True
            raise

    def write_frame_loop(self):
        try:
            duration = 1.0/self.writer.fps
            last_time = time.time()
            self._stop_flag = False
            while True:
                if time.time()-last_time >= duration:
                    last_time += duration
                    try:
                        self.writer.write(self.tmp_frame)
                    except Exception as e:
                        print(f"Error writing frame: {e}")
                        break
                if self.is_stop():
                    break
                time.sleep(0.0001)
            self.writer.close()
            self._stop_flag = True
        except Exception as e:
            print("write thread error", e)
            self._stop_flag = True
            self.writer.close()  # Ensure the writer is closed on error
            raise
