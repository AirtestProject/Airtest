# _*_ coding:UTF-8 _*_
import socket
import os
import struct
import subprocess as sp
import wire_pb2
import time
from threading import Thread
from Queue import Queue

APP_PATH = 'jp.co.cyberagent.stf'
SCREENCAP_SERVICE = 'jp.co.cyberagent.stf.Agent'
SERVICE_FORWARD_PORT = 9998
AGENT_FORWARD_PORT = 9999


def start_service():
    export_cmd = ["adb", "shell", "am", 'startservice', '--user', '0', '-a', 'jp.co.cyberagent.stf.ACTION_START', '-n', 'jp.co.cyberagent.stf/.Service']
    os.system(sp.list2cmdline(export_cmd))
    forward_cmd = ["adb", "forward", "tcp:%s" % SERVICE_FORWARD_PORT, "localabstract:stfservice"]
    os.system(sp.list2cmdline(forward_cmd))


def start_agent():
    path = get_path()
    cmd = ["adb", "shell", "CLASSPATH=" + path, 'exec', 'app_process', '/system/bin', SCREENCAP_SERVICE, ]
    os.system(sp.list2cmdline(cmd))
    forward_cmd = ["adb", "forward", "tcp:%s" % AGENT_FORWARD_PORT, "localabstract:stfagent"]
    os.system(sp.list2cmdline(forward_cmd))


def get_path():
    cmd = ["adb", "shell", "pm", "path", APP_PATH]
    output = sp.check_output(cmd)
    if len(output) == 1:
        path = output[0]
        return path.split('\r')[0]
    else:
        return ""


def wake_packet():
    e = wire_pb2.Envelope()
    e.type = wire_pb2.GET_SD_STATUS
    e.message = wire_pb2.GetSdStatusRequest().SerializeToString()
    data = e.SerializeToString()
    return data


def unpacket(b):
    e = wire_pb2.Envelope()
    e.ParseFromString(b)
    print(e)
    if e.type in REGISTRY:
        callback = REGISTRY[e.type]
        print(callback)
        callback(e.type, e.message)
    return e


REGISTRY = {}


def register(message_type, callback):
    REGISTRY[message_type] = callback


def unregister(message_type):
    REGISTRY.pop(message_type)


def wait_for(message_type, timeout=None):
    wait_time, interval = 0, 0.5
    output = []
    def callback(message_type, message):
        output.append(message)
        unregister(message_type)
    register(message_type, callback)
    while message_type in REGISTRY:
        time.sleep(interval)
        wait_time += interval
        if timeout is not None and wait_time >= timeout:
            return False
    print(output)
    return output[0]


INPUT_QUEUE = Queue()


def send(data):
    b = struct.pack('<B', len(data)) + data
    INPUT_QUEUE.put(b)


class stream_reader(object):

    def __init__(self):
        super(stream_reader, self).__init__()
        self.buf = b''

    def input(self, chunk):
        self.buf += chunk

    def output(self):
        '''
        to be fixed: assume one byte of length here
        '''
        if len(self.buf) == 0:
            return None
        length = self.buf[0]
        length = struct.unpack('<B', length)[0]
        if len(self.buf) - 1 < length:
            return None
        content, self.buf = self.buf[1: length+1], self.buf[length+1:]
        return content


def on_battery_event(message_type, message):
    print("on_battery_event", message)
    message_obj = wire_pb2.BatteryEvent()
    message_obj.ParseFromString(message)
    print(message_obj)


def on_sd_status_event(message_type, message):
    message_obj = wire_pb2.GetSdStatusResponse()
    message_obj.ParseFromString(message)
    print(message_obj)


def init_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 9998))
    s.setblocking(False)
    data = wake_packet()
    send(data)

    reader = stream_reader()

    def bg_worker():
        while True:
            while INPUT_QUEUE.qsize() > 0:
                data = INPUT_QUEUE.get()
                print('send', repr(data))
                sent = 0
                while sent < len(data):
                    sent += s.send(data)
            try:
                r = s.recv(4096)
            except socket.error:
                continue
            print(repr(r))
            if r == '':
                raise socket.error("connection broken")
            elif r:
                reader.input(r)
            response = reader.output()
            if response is None:
                time.sleep(0.1)
                continue
            res_obj = unpacket(response)
    t = Thread(target=bg_worker)
    t.daemon = True
    t.start()


def test_client():
    register(wire_pb2.EVENT_BATTERY, on_battery_event)
    register(wire_pb2.GET_SD_STATUS, on_sd_status_event)
    init_connection()
    time.sleep(2)
    message = wait_for(wire_pb2.EVENT_ROTATION)
    message_obj = wire_pb2.RotationEvent()
    message_obj.ParseFromString(message)
    print(message_obj)


if __name__ == '__main__':
    # start_service()
    # start_agent()
    test_client()
