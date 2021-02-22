#!/usr/bin/python
# coding=utf-8

import sys
import serial
import time
import logging
import struct
import datetime

# for debug
import pprint

sys.path.append('/root/8036/pycharm-debug.egg')
import pydevd
pydevd.settrace('192.168.8.100', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
#pydevd.settrace('192.168.7.8', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)

logging.basicConfig(level=logging.DEBUG, filename="./log.log")
logging.debug('A debug message!')

ser = serial.Serial()
ser.port = "/dev/ttyS0"
ser.baudrate = 9600
ser.bytesize = 8  #number of bits per bytes
ser.stopbits = 2  #number of stop bits
ser.timeout = 2
ser.parity = serial.PARITY_NONE  #set parity check: no parity
ser.xonxoff = False  #disable software flow control
ser.rtscts = False  #disable hardware (RTS/CTS) flow control
ser.dsrdtr = False  #disable hardware (DSR/DTR) flow control
ser.writeTimeout = 1  #timeout for write
#ser.flowControlOut = False

# Serial port object
#print("obj(ser) after properties: ")
#pprint.pprint(ser)

read_loop_max = 10 # Количество перечитываний данных из контроллера, после которого, если контроллер вернул некорректные данные, выводить сообщение об ошибке

print ' ----------------------------------------------'
print ' --- START TEST 2 ---'

try:
    ser.open()
except Exception, e:
    print "error open serial port: " + str(e)
    exit()

if ser.isOpen():
    try:
        # Проверка того, что контроллер отвечает, если не отвечает вываливаться с ошибкой (генерировать исключение)
        ser.flush()
        ser.write("b")
        result_raw = ser.read(2)
        if len(result_raw)!=2:
            raise "Error: контроллер не отвечает"

        ########################################################################
        # 3. ‘l’ Чтение логического состояния выходов (не зависимо от импульсного режима)
        # Команда: 1 байт – ASCII-символ ‘l’
        # Ответ: 2 байтное число, каждый бит которого соответствует состоянию нагрузки.
        # 11 бит соответствует 1 выходу,
        # 10 бит – 2 выходу
        # и т.д. до 0 бита, который соответствует 12 выходу
        ########################################################################
        print ' --- 3.Logical status of outputs ---'
        ser.flush()
        ser.write("l")
        result_raw = ser.read(2)
        #temp1 = ord(result_raw[0])
        #temp2 = ord(result_raw[1])
        print("outputs state 0byte (BIN) >> " + '{0:08b}'.format(ord(result_raw[0])))
        print("outputs state 1byte (BIN) >> " + '{0:08b}'.format(ord(result_raw[1])))
        #print("outputs state (BIN) >> " + '{0:08b}'.format(ord(result_raw[1])) + '{0:08b}'.format(ord(result_raw[0])))

        #print("outputs state (DEX) >> " + str(ord(result_raw[0])) + " " + str(ord(result_raw[1])))

        ########################################################################
        # 4. ‘z’ Чтение реального состояния выходов в данный конкретный момент
        # Команда: 1 байт – ASCII-символ ‘z’
        # Ответ: 2 байтное число, каждый бит которого соответствует состоянию выхода:
        # 11 бит сопоставлен 1 выходу,
        # 10 бит – 2 выходу
        # и т.д. до 0 бита, который соответствует 12 выходу
        ########################################################################

        print ' --- 4.Real status on outputs - --'
        ser.flush()
        ser.write("z")
        result_raw = ser.read(2)
        actuators_status_raw = "{:08b}".format(ord(result_raw[1])) + "{:08b}".format(ord(result_raw[0]))
        actuators_status = actuators_status_raw[4:15]
        act_one_1 = actuators_status[0]
        act_one_2 = actuators_status[1]
        act_one_3 = actuators_status[2]
        act_one_4 = actuators_status[3]
        act_one_5 = actuators_status[4]
        act_one_6 = actuators_status[5]
        act_one_7 = actuators_status[6]
        act_one_8 = actuators_status[7]

        print("outputs state (BIN) >> " + '{0:08b}'.format(ord(result_raw[1])) + '{0:08b}'.format(ord(result_raw[0])))
        print("After BIN mask")
        test = ord(result_raw[1]) + (ord(result_raw[0]) << 8)
        test1 = test & 0b0000111111111111
        print("outputs state (BIN) >> " + bin(test1))
        # seconds = ((ord(result_raw[0]) & 0b01110000) >> 4) * 10 + (ord(result_raw[0]) & 0b00001111)
        # print("outputs state (BIN) >> " + '{0:b}'.format(result_raw))
        #print("outputs state (DEX) >> " + str(ord(result_raw[0])) + " " + str(ord(result_raw[1])))
        PingOutState = {}
        PinConnections = [12,11,10,9,8,7,6,5,4,3,2,1]
        for PinId in PinConnections:
            PinMask = 1 << PinId
            PingOutState[PinId] = (test1 & PinMask) >> PinId
            if PingOutState[PinId] == 1:
                print ("State(" + str(PinId) + ")=On")
            else:
                print ("State(" + str(PinId) + ")=Off")



    except  Exception,  e1:
        print "error communicating...: " + str(e1)

    ser.close()
else:
    print "cannot open serial port "
