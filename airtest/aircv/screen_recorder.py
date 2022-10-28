import cv2
import ffmpeg
import threading
import time
import numpy as np


class VidWriter:
    def __init__(self, outfile, width, height, mode='ffmpeg', fps=10):
        self.mode = mode
        self.fps = fps
        self.vid_size = max(width, height)
        if self.vid_size % 32 != 0:
            self.vid_size = self.vid_size - (self.vid_size % 32) + 32
        self.cache_frame = np.zeros(
            (self.vid_size, self.vid_size, 3), dtype=np.uint8)
        width, height = self.vid_size, self.vid_size
        if self.mode == "ffmpeg":
            from airtest.core.ffmpeg import ffmpeg_setter
            ffmpeg_setter.add_paths()
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
        elif self.mode == "cv2":
            fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
            self.writer = cv2.VideoWriter(outfile, fourcc, self.fps, (width, height))

    def write(self, frame):
        assert len(frame.shape) == 3
        if self.mode == "ffmpeg":
            frame = frame[..., ::-1]
        self.cache_frame[:frame.shape[0], :frame.shape[1], :] = frame.astype(np.uint8)
        self.writer.write(self.cache_frame)

    def close(self):
        if self.mode == "ffmpeg":
            self.writer.close()
            self.process.wait()
            self.process.terminate()
        elif self.mode == "cv2":
            self.writer.release()


class ScreenRecorder:
    def __init__(self, outfile, get_frame_func, mode='ffmpeg', fps=10,
                 snapshot_sleep=0.001):
        self.get_frame_func = get_frame_func
        self.tmp_frame = self.get_frame_func()
        self.snapshot_sleep = snapshot_sleep
        width, height = self.tmp_frame.shape[1], self.tmp_frame.shape[0]
        self.writer = VidWriter(outfile, width, height, mode, fps)
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

    def start(self, mode="two_thread"):
        if self._is_running:
            print("recording is already running, please don't call again")
            return False
        self._is_running = True
        if mode == "one_thread":
            self.t_stream = threading.Thread(target=self.get_write_frame_loop)
            self.t_stream.setDaemon(True)
            self.t_stream.start()
        else:
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

    def get_frame_loop(self):
        # 单独一个线程持续截图
        try:
            while True:
                self.tmp_frame = self.get_frame_func()
                time.sleep(self.snapshot_sleep)
                if self.is_stop():
                    break
            self._stop_flag = True
        except Exception as e:
            print("record thread error", e)
            self._stop_flag = True
            raise

    def write_frame_loop(self):
        # 按帧率间隔获取图像写入视频
        try:
            duration = 1.0/self.writer.fps
            last_time = time.time()
            self._stop_flag = False
            while True:
                if time.time()-last_time >= duration:
                    self.writer.write(self.tmp_frame)
                    last_time = time.time()
                if self.is_stop():
                    break
                time.sleep(0.0001)
            self.writer.close()
            self._stop_flag = True
        except Exception as e:
            print("write thread error", e)
            self._stop_flag = True
            raise

    def get_write_frame_loop(self):
        # 同时截图并写入视频
        try:
            duration = 1.0/self.writer.fps
            last_time = time.time()
            self._stop_flag = False
            while True:
                now_time = time.time()
                if now_time - last_time >= duration:
                    if now_time - last_time < duration+0.01:
                        self.tmp_frame = self.get_frame_func()
                    self.writer.write(self.tmp_frame)
                    last_time += duration
                if self.is_stop():
                    break
                time.sleep(0.0001)
            self._stop_flag = True
            self.writer.close()
        except Exception as e:
            print("record and write thread error", e)
            self._stop_flag = True
            raise
