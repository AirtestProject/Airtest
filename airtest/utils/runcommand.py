import subprocess
import traceback
import json
from six import string_types
from airtest.utils.logger import get_logger

LOGGING = get_logger(__name__)

def runcommand(cmds, silent=False):
    '''执行CMD命令返回结果'''
    output = None
    if cmds:
        try:
            cmds = cmds.split() if isinstance(cmds, string_types) else list(cmds)
            if silent:
                output = subprocess.check_output(cmds, stderr=subprocess.DEVNULL)
            else:
                output = subprocess.check_output(cmds)
            output = output.strip().decode('utf-8', "replace")
        except Exception:
            LOGGING.error("CMD excute failed: {}".format(cmds))
    return output


def runcommand_with_json_output(cmds):
    output = runcommand(cmds)
    if not output:
        return None
    
    try:
        return json.loads(output)
    except Exception as e:
        LOGGING.error(f"Failed to parse output of {cmds} command: {output}")
        return None


def run_background(*args, **kwargs):
    '''
    以后台进程的方式执行命令，并返回句柄
    '''
    silent = kwargs.pop('silent', False)
    if silent:
        kwargs['stdout'] = subprocess.DEVNULL
        kwargs['stderr'] = subprocess.DEVNULL
    LOGGING.info("exec: %s", subprocess.list2cmdline(args[0]))
    p = subprocess.Popen(*args, **kwargs)
    return p


def run_background_with_pipe(cmd1, cmd2):
    p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    return p2
