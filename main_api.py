#!/usr/bin/python
# coding=utf-8

import threading
import sys
import signal
import config
import time, datetime
#import sys
#import struct
#from flask import jsonify
#from api_utils import ResponsiveFlask
#import atexit


# my modules ------------
#from HeatController.Controller8036 import *
from ServerAPI.ServerAPI import *

print(" --- Start main_api.py ---")
if config.debug_enable:
    # for debug
    print("DEBUG mode: enable ---------------------------------------")
    import pprint
    from var_dump import var_dump
    sys.path.append('/root/8036/pycharm-debug.egg')
    import pydevd
    pydevd.settrace(config.debug_pydevd_host, port=config.debug_pydevd_port, stdoutToServer=True, stderrToServer=True, suspend=False)


class Main():
    def __init__(self):
        self.exit_flag = False
        self.heat_controller = Controller8036()  # Начальная инициализация
                                                 # (вне потоков, что-бы нормально настроить порт и прочее)
        self.httpAPI = ServerAPI()
        self.testTHR = threading.Thread(target=self.heartbeat_test, args=(5,))
        self.testTHR.setName("heartbeat_test_thread")
        self.StatCollectorTHR = threading.Thread(target=self.statistic_collector, args=(config.periodicity_collection,))
        self.StatCollectorTHR.setName("statistic_collector_thread")

    def do_quit(self, *args, **kwargs):
        '''
        Корректное завершение всех процессов (те, что отдельными тредами запущены)
        :param args:
        :param kwargs:
        :return:
        '''
        self.exit_flag = True
        print "\nQuit\n"
        print "\nWait stop all threads...\n"

        self.httpAPI.stop()
        self.testTHR.join()
        self.testTHR.isAlive()
        self.StatCollectorTHR.join()
        self.StatCollectorTHR.isAlive()
        exit()

    def do_sleep(self, sleepTime=1):
        '''
        Хак функции sleep для того, что-бы во время ожидания окончания времени осуществлялась
        проверка на поднятие флага завершения работы
        :return; True если поднят флаг завершения работы
        '''
        while sleepTime > 0:
            sleepTime -= 1
            if self.exit_flag:
                print("\n thread: is stopped")
                return True
            time.sleep(1)

    def heartbeat_test(self, sleepTime=3):
        loop = 0
        while True:
            loop += 1
            print(str(datetime.datetime.now()) + " Heartbeat message: Loop: " + str(loop))
            if self.do_sleep(sleepTime):
                return

    def statistic_collector(self, sleepTime=3600):
        '''
        Периодический сбор данных для статистики
        :param timeUpdate: периодичность сбора данных (в секундах)
        :return: '''
        print "\n - StatisticCollector\n"

        #while True: # Отключили сбор статистики
        #    pass
        while True:
            result = self.heat_controller.UpdateSensorsHistory()
            if result['error']:
                print("\n Ошибка сохранения статистики. Error message:" + result['error_message'])
            year, month, day, weekday, hours, minutes, seconds = self.heat_controller.get_datetime()
            # TODO Проверить, если разница времени котроллера и времени сервера более чем на заданное значение, произвести синхронизацию времени
            if self.do_sleep(sleepTime):
                return

    def start(self):
        '''
        Начало работы основной программы
        :return:
        '''
        self.testTHR.start()
        self.StatCollectorTHR.start()

        # Включаем обработку системных сигналов (сигнал QUIT)
        #atexit.register(self.goodbye)
        signal.signal(signal.SIGINT, self.do_quit)
        signal.signal(signal.SIGTERM, self.do_quit)
        signal.signal(signal.SIGQUIT, self.do_quit)

        # Запускаем web сервер для API вызовов
        # --- HTTP API Server ----------------------
        self.httpAPI.start()
        #mainLoop = 0
        #while True:
        #    mainLoop += 1
        #    print(str(datetime.datetime.now()) + " Loop message: mainLoop: " + str(mainLoop))
        #    time.sleep(3)

        #while True:
        #    time.sleep(1)

main = Main()
main.start()
