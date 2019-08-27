# -*- coding: utf-8 -*-
import subprocess
import time
import sys
import random
from airtest.core.error import AirtestError
from airtest.utils.snippet import reg_cleanup, on_method_ready, get_std_encoding
from airtest.utils.logger import get_logger
from airtest.utils.retry import retries

LOGGING = get_logger(__name__)


class InstructHelper(object):
    """
    ForwardHelper class
    or help run other Instruction
    """

    proxy_process = 'iproxy'

    def __init__(self):
        self.subprocessHandle = []
        reg_cleanup(self.teardown)

    @on_method_ready('start')
    def get_ready(self):
        pass

    def teardown(self):
        # stop all process started by self
        for sub_proc in self.subprocessHandle:
            sub_proc.kill()

    # this function auto gen local port
    @retries(3)
    def setup_proxy(self, remote_port):
        local_port = random.randint(11111, 20000)
        self.do_proxy(local_port, remote_port)
        return local_port, remote_port

    def do_proxy(self, local_port, remote_port):
        """
        Start do proxy of ios device and self device

        Returns:
            None

        """

        cmds = [self.proxy_process, str(local_port), str(remote_port)]

        proc = subprocess.Popen(
            cmds,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # something like port binding fail
        time.sleep(0.5)

        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            stdout = stdout.decode(get_std_encoding(sys.stdout))
            stderr = stderr.decode(get_std_encoding(sys.stderr))
            raise AirtestError((stdout, stderr))

        self.subprocessHandle.append(proc)

if __name__ == '__main__':
    ins = InstructHelper()
    ins.do_proxy(8100, 8100)
