import pydevd
pydevd.settrace('192.168.7.202', port=5678, stdoutToServer=True, stderrToServer=True)
