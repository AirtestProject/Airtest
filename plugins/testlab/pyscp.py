import paramiko
from scp import SCPClient



def connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.40.218', 32200, 'gzliuxin', key_filename=r'C:\Users\game-netease\Desktop\gzliuxin')
    return ssh

def ls():
    ssh = connect()
    stdin, stdout, stderr = ssh.exec_command('ls')
    print stdout.readlines()


def upload(src, dst):
    ssh = connect()
    with SCPClient(ssh.get_transport()) as scp:
        scp.put(src, dst, recursive=True)


if __name__ == '__main__':
    import os
    os.chdir(r"I:\jenkins\workspace\run_one_pipe")
    upload(".", "/home/gzliuxin/testlab/0")
