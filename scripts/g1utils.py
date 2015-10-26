import requests
HOST, PORT = "192.168.10.191", 17800
USERNUM = 31996757

def server_call(cmd):
    r = requests.post("http://192.168.11.243:8015/webcmd", data={
            "serverport": PORT,
            "serverip": HOST,
            "usernum": USERNUM,
            "content": cmd
        })
    return r.text


if __name__ == '__main__':
    server_call("$at h")
    print server_call("at/G1/sm/main->get_sm_leaf(\"$id@89\")")
