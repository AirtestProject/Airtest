from subprocess import Popen, PIPE, STDOUT
from moa.core.utils import NonBlockingStreamReader as nbsp
import time

proc = Popen("python -m moa.airtest_runner wtf --setsn --forever", shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
proc_stdout = nbsp(proc.stdout)
while True:
    proc_output_line = proc_stdout.readline(5.0)
    if proc_output_line is None:
        raise RuntimeError("something wrong")
    if proc_output_line.startswith("wait for stdin"):
        break
print "start to rock"
while True:
    line = raw_input("what is next?\n") + "\n"
    proc.stdin.write(line)
    proc.stdin.flush()
