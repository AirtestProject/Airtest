from airtest.moa.moa import exec_script
import sys
filename = sys.argv[1]
with open(filename) as f:
    code = f.read()
# print code
exec_script(code)
