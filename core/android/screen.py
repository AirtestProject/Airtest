import core
import sys
import time

core.PROJECTIONRATE = 1
sn = core.adb_devices(state="device").next()[0]
device = core.Android(sn)
mi = device.minicap


from flask import Flask, render_template, Response


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('video.html')

def gen():
    gener = mi.get_frames(max_cnt=3000000)
    header = gener.next()
    cnt = 0
    while True:
        frame = gener.next()
        cnt += 1
        # time.sleep(0.03)
        print cnt
        sys.stdout.flush()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
        mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # app.run(host='0.0.0.0', debug=True)
    from gevent.wsgi import WSGIServer
    http_server = WSGIServer(('', int(5001)), app)
    http_server.serve_forever()
