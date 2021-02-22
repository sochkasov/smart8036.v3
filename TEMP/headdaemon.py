#!/usr/bin/python
# coding=utf-8

import sys

# for debug
sys.path.append('/root/8036/pycharm-debug.egg')
import pydevd
pydevd.settrace('192.168.8.100', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
#pydevd.settrace('192.168.7.8', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)


# def main():
#     print("loop")
#     HeadController = Controller8036()
#     if HeadController.testConnection() != True:
#         print("Error. No connect to Heat controller")
#     else:
#         print("Connect is success")
#
# while True:
#     try:
#         main()
#     except:
#         print("Unknown ERROR")
#         pass
#     finally:
        #time.sleep( 2 ) # 1 min.
