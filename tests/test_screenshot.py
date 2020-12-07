import requests
import base64



if __name__ == '__main__':
    url = 'http://10.251.100.86:20003/screenshot'
    r= requests.get(url)
    value = r.json()['value']
    raw_value = base64.b64decode(value)
    filename33 = "test33.jpg"
    with open(filename33, 'wb') as f:
        f.write(raw_value)