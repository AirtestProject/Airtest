import re
import socket


HOST, PORT = "192.168.10.104", 27030
USERNUM = 31996757


def _send(msg, host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((host, port))
    s.sendall(msg)
    reply = s.recv(4096).decode('gbk')
    s.close()
    return reply


def _remote_qc_call(ip, port, file_func):
    msgstr = """remote_qc_call %s\n""" % file_func
    result = _send(msgstr, ip, port)
    return result


def _call(ip, port, usernum, cmdstr):
    cmdstr = cmdstr.strip().lstrip("$").replace("$id", str(usernum))
    m = re.match(r"(\w|\/)+->\w+\((.*)\)", cmdstr)
    if m:
        file_func_str = cmdstr
    else:
        def _cmd_to_file_func(usernum, cmdstr):
            file_func_str = """cmd/wizcmd->command(%s, "%s", 0)""" % (usernum, cmdstr)
            return file_func_str
        file_func_str = _cmd_to_file_func(usernum, cmdstr)
    return _remote_qc_call(ip, int(port), file_func_str)


def server_call(cmd, host=HOST, port=PORT, usernum=USERNUM):
    _call(host, port, usernum, cmd)


if __name__ == '__main__':
    server_call("$at h")
