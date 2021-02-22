# coding=utf-8
#from decimal import *

import config
import db
from HeatController.Controller8036 import *
#import HeatController


class Step_program(object):
    time_on_h = 0
    time_on_m = 0
    time_on_s = 0
    time_off_h = 0
    time_off_m = 0
    time_off_s = 0
    time_on_day = 0
    time_off_day = 0
    time_on_month = 0
    time_off_month = 0
    time_on_year = 0
    time_off_year = 0
    time_load = 0
    time_loadsensor = 0
    time_min = 0
    time_max = 0
    time_mode = 0
    time_eze = 0
    time_ezedata = 0
    time_bud = 0
    enable = 0
    sensortype = 0

def __init__(self):
    pass


class Hot_controller_program(object):

    dict_time_mode = {0: "Нагрев", 1: "Охлаждение", 2: "Buzzer", 3: "Таймер"}
    dict_time_eze = {0: "Без периода", 1: "По дням", 2: "По дням недели", 3: "По месяцам"}
    dict_sensortype = {0: "DS18B20", 1: "Analog", 2: "", 3: ""}
    dict_enable = {0: "Выкл", 1: "Вкл"}

    def __init__(self, obj):
        #self.ctl8036 = Controller8036()
        self.ctl8036 = obj
        #self.dbconnect = db.Database()
        pass

    def decode_from_raw(self, raw_program):
        step = dict()
        for i in range(0, 32, 1):
            result_get = raw_program[i*27:i*27+27]
            print('{:0>2d}'.format(i) + ': ' + str(result_get.encode("HEX")))  # Вывод кода программы в бинарном виде
            step[i] = Step_program()
            # step[i].time_on_h =         ord(result_get[0])
            step[i].time_on_h =         ord(result_get[0])
            step[i].time_on_m =         ord(result_get[1])
            step[i].time_on_s =         ord(result_get[2])
            step[i].time_off_h =        ord(result_get[3])
            step[i].time_off_m =        ord(result_get[4])
            step[i].time_off_s =        ord(result_get[5])
            step[i].time_on_day =       ord(result_get[6])
            step[i].time_off_day =      ord(result_get[7])
            step[i].time_on_month =     ord(result_get[8])
            step[i].time_off_month =    ord(result_get[9])
            step[i].time_on_year =      ord(result_get[10])
            step[i].time_off_year =     ord(result_get[11])
            step[i].time_load =         ord(result_get[12])
            step[i].time_loadsensor =   ord(result_get[13])
            # TODO проверить на правильность отображения температуры при отрицательных значениях температуры в программе
            if ord(result_get[14]) != 0 and ord(result_get[15]) != 0:
                step[i].time_min = float(ord(result_get[14]) + (ord(result_get[15]) << 8))*0.01
            else:
                step[i].time_min = 0
            if ord(result_get[16]) != 0 and ord(result_get[17]) != 0:
                step[i].time_max = float(ord(result_get[16]) + (ord(result_get[17]) << 8))*0.01
            else:
                step[i].time_max = 0
            step[i].time_mode =         ord(result_get[18])
            step[i].time_eze =          ord(result_get[19])
            step[i].time_ezedata =      ord(result_get[23]) + \
                                        ord(result_get[22]) << 8 + \
                                        ord(result_get[21]) << 16 + \
                                        ord(result_get[20]) << 24
            step[i].time_bud =          ord(result_get[24])
            step[i].enable =            ord(result_get[25])
            step[i].sensortype =        ord(result_get[26])

            mode_txt = self.dict_time_mode.get(step[i].time_mode)
            enable_txt = self.dict_enable.get(step[i].enable)
            sensortype_txt = self.dict_sensortype.get(step[i].sensortype)
            if config.debug_enable:
                print('Program(' + str(i) + ') '+enable_txt+' '+mode_txt+' '+sensortype_txt+' Start: ' \
                      + str(2000+step[i].time_on_year) + '.' + '{:0>2d}'.format(step[i].time_on_month) + '.' + '{:0>2d}'.format(step[i].time_on_day) + ' ' \
                      + '{:0>2d}'.format(step[i].time_on_h) + ':' + '{:0>2d}'.format(step[i].time_on_m) + ':' + '{:0>2d}'.format(step[i].time_on_s) \
                      + ' Stop: ' \
                      + str(2000+step[i].time_off_year) + '.' + '{:0>2d}'.format(step[i].time_off_month) + '.' + '{:0>2d}'.format(step[i].time_off_day) + ' ' \
                      + '{:0>2d}'.format(step[i].time_off_h) + ':' + '{:0>2d}'.format(step[i].time_off_m) + ':' + '{:0>2d}'.format(step[i].time_off_s) \
                      + ' L(' + str(step[i].time_load) + ')' \
                      + ' Sensor(' + str(step[i].time_loadsensor+1) + ')' \
                      + ' t ' + str(step[i].time_min) \
                      + '...' + str(step[i].time_max) + ' ˚C' \
                      )

        #print(str(step))
        return step


    def decode_from_raw_tuple(self, raw_program):
        result = []
        for i in range(0, 32, 1):
            step = {}
            result_get = raw_program[i*27:i*27+27]
            if config.debug_enable:
                print('{:0>2d}'.format(i) + ': ' + str(result_get.encode("HEX")))  # Вывод кода программы в бинарном виде
            step['prog_step'] = i
            step['time_on_h'] = ord(result_get[0])
            step['time_on_h'] =         ord(result_get[0])
            step['time_on_m'] =         ord(result_get[1])
            step['time_on_s'] =         ord(result_get[2])
            step['time_off_h'] =        ord(result_get[3])
            step['time_off_m'] =        ord(result_get[4])
            step['time_off_s'] =        ord(result_get[5])
            step['time_on_day'] =       ord(result_get[6])
            step['time_off_day'] =      ord(result_get[7])
            step['time_on_month'] =     ord(result_get[8])
            step['time_off_month'] =    ord(result_get[9])
            step['time_on_year'] =      ord(result_get[10])
            step['time_off_year'] =     ord(result_get[11])
            step['time_load'] =         ord(result_get[12])
            step['time_loadsensor'] =   int(ord(result_get[13]))+1
            sensor_data = self.ctl8036.get_sensor_id_param_from_db(step['time_loadsensor'])
            if sensor_data['error']:
                return sensor_data
            step.update(sensor_data['result'])  # Добавили информацию по датчику из БД
            actuator_data = self.ctl8036.get_actuator_id_param_from_db(step['time_load'])
            if actuator_data['error']:
                return actuator_data
            step.update(actuator_data['result'][0])  # Добавили информацию по нагрузке из БД
            # TODO проверить на правильность отображения температуры при отрицательных значениях температуры в программе
            if ord(result_get[14]) != 0 and ord(result_get[15]) != 0:
                step['time_min'] = round(float(ord(result_get[14]) + (ord(result_get[15]) << 8))*0.01, 2)
            else:
                step['time_min'] = 0
            if ord(result_get[16]) != 0 and ord(result_get[17]) != 0:
                #step['time_max'] = int(float(ord(result_get[16]) + (ord(result_get[17]) << 8)))*0.01
                step['time_max'] = round(float(ord(result_get[16]) + (ord(result_get[17]) << 8))*0.01, 2)
            else:
                step['time_max'] = 0
            step['time_mode'] =         ord(result_get[18])
            step['time_mode_txt'] = self.dict_time_mode.get(step['time_mode'])
            step['time_eze'] =          ord(result_get[19])
            step['time_eze_txt'] = self.dict_time_eze.get(step['time_eze'])
            # step['time_ezedata'] =      ord(result_get[23]) + \
            #                             ord(result_get[22]) << 8 + \
            #                             ord(result_get[21]) << 16 + \
            #                             ord(result_get[20]) << 24
            step['time_ezedata'] = "{:08b}".format(ord(result_get[20])) \
                                   + "{:08b}".format(ord(result_get[21])) \
                                   + "{:08b}".format(ord(result_get[22])) \
                                   + "{:08b}".format(ord(result_get[23]))
            step['time_bud'] = "{:08b}".format(ord(result_get[24]))  # Служебные данные (не менять)
            step['enable'] = ord(result_get[25])
            step['enable_txt'] = self.dict_enable.get(step['enable'])
            step['sensortype'] = ord(result_get[26])
            step['sensortype_txt'] = self.dict_sensortype.get(step['sensortype'])
            print('Program(' + str(i) + ') '+step['enable_txt']+' '+step['time_mode_txt']+' '+step['sensortype_txt']+' Start: ' \
                  + str(2000+step['time_on_year']) + '.' + '{:0>2d}'.format(step['time_on_month']) + '.' + '{:0>2d}'.format(step['time_on_day']) + ' ' \
                  + '{:0>2d}'.format(step['time_on_h']) + ':' + '{:0>2d}'.format(step['time_on_m']) + ':' + '{:0>2d}'.format(step['time_on_s']) \
                  + ' Stop: ' \
                  + str(2000+step['time_off_year']) + '.' + '{:0>2d}'.format(step['time_off_month']) + '.' + '{:0>2d}'.format(step['time_off_day']) + ' ' \
                  + '{:0>2d}'.format(step['time_off_h']) + ':' + '{:0>2d}'.format(step['time_off_m']) + ':' + '{:0>2d}'.format(step['time_off_s']) \
                  + ' L(' + str(step['time_load']) + ')' \
                  + ' Sensor(' + str(step['time_loadsensor']) + ')' \
                  + ' t ' + str(step['time_min']) \
                  + '...' + str(step['time_max']) + ' ˚C' \
                  + ' time_eze: ' + str(step['time_eze']) \
                  + ' ezedata: ' + str(step['time_ezedata']) \
                   + ' time_bud:' + str(step['time_bud']) \
                  )

            if config.debug_enable:
                pass
            result.append(step)
        return {'result': result, 'error': False, 'error_message': ''}

    def encode_to_raw(self):
        pass