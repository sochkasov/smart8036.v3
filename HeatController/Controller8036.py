# coding=utf8
import serial
import struct
import db
import mqtt
import time
import datetime
import config
from HeatController.program import Hot_controller_program
from FreezeStruct import FreezeStruct


class Controller8036(object):
    connection = None
    port_busy = None

    def __new__(cls, *args, **kwargs):
        '''
        Делаем Singletone
        :param args:
        :param kwargs:
        :return:
        '''
        if not hasattr(cls, 'instance'):
            cls.instance = super(Controller8036, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.dbconnect = db.Database()
        self.mqtt = mqtt.MQTT()
        self.prg = Hot_controller_program(self)
        self.controller_fr_struct = FreezeStruct()
        # Если соединение с контроллером еще не выполнялось
        if not self.connection:
            try:
                print(" - Setup SERIAL parameters\n")
                self.ser = serial.Serial()
                self.ser.port = config.hot_controller_port
                self.ser.baudrate = 9600
                self.ser.bytesize = 8  # number of bits per bytes
                self.ser.stopbits = 2  # number of stop bits
                self.ser.timeout = 2
                self.ser.parity = serial.PARITY_NONE  # set parity check: no parity
                self.ser.xonxoff = False  # disable software flow control
                self.ser.rtscts = False  # disable hardware (RTS/CTS) flow control
                self.ser.dsrdtr = False  # disable hardware (DSR/DTR) flow control
                self.ser.writeTimeout = 1  # timeout for write
                # Установка параметров порта и его открытие
                self.ser.open()
                self.port_busy = False
                # Проверка соединения с контроллером
                if self.testConnection():
                    # global DEBUG
                    # if DEBUG:
                    print("OK: Connection with the heat controller is successfully established\n")
                    self.connection = True
                else:
                    print("ERROR: No connect to Heat controller on port " + self.ser.port + "\n")
                    self.connection = False
            except Exception, e:
                print "ERROR: Can not open serial port " + str(self.ser.port) + ": " + str(e) + "\n"
                return None
        return None

    def _read_serial(self, count=1):
        '''
        Чтение из порта нужного количество байт с проверкой порта на занятость
        :param count: количество байт, которые нужно прочитать
        :return:
        '''
        loop = 100  # Количество циклов ожидания освобождения порта
        while self.port_busy:
            time.sleep(0.01)
            loop -= 1
            if loop <= 0:
                return False
        self.port_busy = True  # Выставим флаг занятости COM(RS232) порта в состояние ЗАНЯТО
        result = self.ser.read(count)
        self.port_busy = False  # Выставим флаг занятости COM(RS232) порта в состояние СВОБОДНО
        return result

    def _write_serial(self, data=""):
        '''
        Запись в порт данных с проверкой порта на занятость
        :param count: количество байт, которые нужно прочитать
        :return:
        '''
        loop = 100  # Количество циклов ожидания освобождения порта
        while self.port_busy:
            time.sleep(0.01)
            loop -= 1
            if loop <= 0:
                return False
        self.port_busy = True  # Выставим флаг занятости COM(RS232) порта в состояние ЗАНЯТО
        self.ser.flush()
        result = self.ser.write(data)
        self.port_busy = False  # Выставим флаг занятости COM(RS232) порта в состояние СВОБОДНО
        return result

    def _do_command_get(self, command='', check_echo='', read_byte=0):
        '''
        Отсыл контроллеру комманды на получение данных и возврат результата. С проверкой занятости порта
        :param command:
        :param read_byte:
        :return: сырые данные от контроллера
        '''
        loop = 100  # Количество циклов ожидания освобождения порта
        while self.port_busy:
            time.sleep(0.01)
            loop -= 1
            if loop <= 0:
                return False
        self.port_busy = True  # Выставим флаг занятости COM(RS232) порта в состояние ЗАНЯТО
        self.ser.write(command)
        if check_echo != '':  # Если нужна проверка ответа "эхо" от контроллера (и тогда отбрасываем 1 байт от ответа)
            loop = 100
            while self.ser.read(1) != check_echo:
                time.sleep(0.01)
                loop -= 1
                if loop <= 0:
                    return False  # Выход по таймауту если не получен эхо-ответ
        print("DEBUG: command:'" + command + "' time(loop)=" + str(loop) + "\n")
        result_raw = self.ser.read(read_byte)
        self.port_busy = False  # Выставим флаг занятости COM(RS232) порта в состояние СВОБОДНО
        if len(result_raw) == read_byte:
            return result_raw
        return False

    def _do_command_set(self, command='', check_echo='', data=''):
        '''
        Отсыл контроллеру комманды на запись данных. С проверкой занятости порта
        :param command:
        :param read_byte:
        :return: сырые данные от контроллера
        '''
        loop = 100  # Количество циклов ожидания освобождения порта
        while self.port_busy:
            time.sleep(0.01)
            loop -= 1
            if loop <= 0:
                return False
        self.port_busy = True  # Выставим флаг занятости COM(RS232) порта в состояние ЗАНЯТО
        self.ser.write(command)
        if check_echo != '':  # Если нужна проверка ответа "эхо" от контроллера (и тогда отбрасываем 1 байт от ответа)
            loop = 100
            while self.ser.read(1) != check_echo:
                time.sleep(0.01)
                loop -= 1
                if loop <= 0:
                    print(
                    "ERROR: command:'" + command + "' timeout за заданное время не получен ожидаемый ответ от контроллера\n")
                    return False  # Выход по таймауту если не получен эхо-ответ
        print("DEBUG: command:'" + command + "' time(loop)=" + str(loop) + "\n")
        result_raw = self.ser.write(data)
        self.port_busy = False  # Выставим флаг занятости COM(RS232) порта в состояние СВОБОДНО
        return result_raw

    def testConnection(self):
        ''' Проверка связи с контроллером и ответ контроллера на тестовый запрос
        :return: True - check OK, False - check fail
        '''
        # Check response controller
        if self._do_command_get('b', '', 2) == False:
            return False
        return True

    def GetSensorsAddress(self):
        ''' Получение адресов датчиков
        :return: Словарь адресов всех зарегистрированнх датчиков
        '''
        # 11. ‘D’ Считывание серийных номеров зарегистрированных датчиков Dallas
        # Команда: 1 байт – ASCII-символ ‘D’
        # Ответ: 1 байт «эхо» - символ ‘D’,
        # после передается 32 поля серийных номеров DS18B20 по 8 байт (суммарно 256 байт),
        # если датчик не зарегистрирован на центральном блоке – то получить его серийный номер не получится
        self._write_serial("D")
        while self._read_serial(1) != "D":
            pass
        result = {}
        # Content in graphical format
        for sensor_id in range(0, 31, 1):
            result_raw = self._read_serial(8)
            addr_string = ""
            addr_byte = ""
            sensor_is_exist = False
            for ind in range(0, len(result_raw), 1):
                addr_byte = "{:02x}".format(int(ord(result_raw[ind])))
                addr_string += str(addr_byte)
                if addr_byte != "00":
                    sensor_is_exist = True
            if sensor_is_exist:
                result[sensor_id] = (addr_string)
        return result

    def GetTemperatureCurrent(self):
        ''' Получение текущей температуры от датчиков
        :return: Словарь с температурами датчиков
        '''
        # 1. ‘t’ Чтение значений температуры
        # Команда: 1 байт – ASCII-символ ‘t’
        # Ответ: 1 байт количество температурных датчиков (32), далее передаются значения температуры всех 32 датчиков.
        # Формат числа int(16-битное знаковое целое число со значением температуры, умноженное на 100).
        result = {}
        result_raw = self._do_command_get('t', chr(32), 64)
        # Если получено не 64 байта, то получаем ошибку
        if len(result_raw) != 64:
            return False, True, 'Поблема получения корректных данных с контроллера 8036'
        for sensor_id in range(0, len(result_raw) / 2, 1):
            sign_temperature_raw = struct.unpack('<h', result_raw[sensor_id * 2] + result_raw[sensor_id * 2 + 1])
            sign_temperature = (float(sign_temperature_raw[0])) / 100
            result[sensor_id] = float(sign_temperature)
        # return result, False, ''
        return {'result': result, 'error': False, 'error_message': ''}

    def GetAddressSensorsTemperature(self):
        ''' Получение словаря с сопоставленными адресов датчиков их текущей температуры
        :return: Словарь значений адресов и значений температуры зарегистрированных датчиков
        '''
        result = {}
        sensor_address = self.GetSensorsAddress()
        sensor_temperatures = self.GetTemperatureCurrent()
        for k, v in sensor_address.iteritems():
            if (sensor_temperatures.has_key(k)):
                result[v] = sensor_temperatures[k]
        return result, False

    def GetSensorsTemperatureIndex(self):
        ''' Получение словаря с сопоставленными id датчиков их адресов, номера связки в БД и текущей температуры
        :return: Словарь значений адресов и значений температуры зарегистрированных датчиков (разбито по индексам)
        '''
        result_array = {}
        sensor_address = self.GetSensorsAddress()
        result = self.GetTemperatureCurrent()
        sensor_temperatures = result['result']
        if result['error']:
            return result
        for k, v in sensor_address.iteritems():
            if (sensor_temperatures.has_key(k)):
                sensor_result = {}
                sensor_result["addr"] = v
                sensor_result["sensor_value"] = sensor_temperatures[k]
                result = self.GetSensorParamFromDB(v)
                if result['error']:
                    return result
                sensor_info = result['result'][0]
                if len(sensor_info) != 0:
                    sensor_result["link_id"] = sensor_info['link_id']
                    result_array[k] = sensor_result
                else:
                    sensor_result["link_id"] = 0
                    print("Info: Sensor is not registered in DB. Address:" + v)
        return {'result': result_array, 'error': False, 'error_message': ''}

    def GetSensorsTemperature(self):
        ''' Получение словаря с сопоставленными id датчиков их адресов, номера связки в БД и текущей температуры
        :return: Словарь значений адресов и значений температуры зарегистрированных датчиков (разбито по индексам)
        '''
        data = []
        sensor_address = self.GetSensorsAddress()
        result = self.GetTemperatureCurrent()
        sensor_temperatures = result['result']
        if result['error']:
            return result
        for k, v in sensor_address.iteritems():
            if (sensor_temperatures.has_key(k)):
                sensor_result = {}
                sensor_result["addr"] = v
                sensor_result["sensor_value"] = sensor_temperatures[k]
                # raw, error, error_message = self.GetSensorParamFromDB(v)
                result = self.GetSensorParamFromDB(v)
                if result['error']:
                    return result
                sensor_info = result['result'][0]  # Справочник датчика из БД
                if len(sensor_info) != 0:
                    sensor_result["link_id"] = sensor_info['link_id']
                    sensor_result["sensor_type"] = sensor_info['sensor_type_name']
                    sensor_result["sensor_place"] = sensor_info['place_name']
                    sensor_result["sensor_notes"] = sensor_info['sensor_notes']
                    sensor_result["sensor_dom_id"] = 'dom_id' + str(sensor_info['link_id'])
                    need_graph_history = True
                    if need_graph_history:
                        sensor_graph_history = self.get_sensor_hostory(sensor_result["link_id"])
                        if sensor_graph_history['error']:
                            sensor_result["graph_history"] = {}  # Нет данных статистики
                        else:
                            sensor_result["graph_history"] = sensor_graph_history['result']  # Статистика
                else:
                    sensor_result["link_id"] = 0
                    print("Info: Sensor is not registered in DB. Address:" + v)
                data.append(sensor_result)
        return {'result': data, 'error': False, 'error_message': ''}

    def GetSensorParamFromDB(self, addr=''):
        '''
        :param addr: Адрес датчика
        :return: Dict данные о датчике из базы
        '''
        if not addr:
            return {'result': '', 'error': True,
                    'error_message': 'GetSensorParamFromDB: Не указан адрес датчика для получения данных addr=""'}
        result = self.dbconnect.ExecuteQuery("SELECT "
                                             "sensors.id as sensor_id, "
                                             "sensors.type as type_id, "
                                             "sensors_parameters_links.id as link_id, "
                                             "sensors.enable as sensor_enable, "
                                             "sensors_parameters_links.hardware_link_id, "
                                             "sensors_parameters_links.place_name as place_name, "
                                             "sensors_parameters_links.sensor_notes as sensor_notes, "
                                             "parameters.name as parameter_name, "
                                             "sensors_type.name as sensor_type_name "
                                             "FROM sensors "
                                             "LEFT JOIN sensors_parameters_links ON sensors_parameters_links.sensor_id=sensors.id "
                                             "LEFT JOIN parameters ON sensors_parameters_links.parameter_id=parameters.id "
                                             "LEFT JOIN sensors_type ON sensors.type=sensors_type.id  "
                                             "WHERE hardware_addr = '" + addr + "'")
        if result['error']:
            return result
        if len(result['result']) > 1:
            print('Error: Exist dublicate sensor link. Sensor addr:' + addr)
        return result

    def get_sensor_id_param_from_db(self, id):
        '''
        :param id: Логический адрес датчика в контроллере
        :return: Dict данные о датчике из базы
        '''
        if not id:
            return {'result': '', 'error': True,
                    'error_message': 'get_sensor_id_param_from_db: Не указан адрес датчика для получения данных id=""'}
        result = self.dbconnect.ExecuteQuery("SELECT "
                                             "sensors.id as sensor_id, "
                                             "sensors.type as sensor_type_id, "
                                             "sensors_parameters_links.id as sensor_link_id, "
                                             "sensors.enable as sensor_enable, "
                                             "sensors_parameters_links.hardware_link_id as sensor_enable_hw_link_id, "
                                             "sensors_parameters_links.place_name as sensor_place_name, "
                                             "sensors_parameters_links.sensor_notes as sensor_notes, "
                                             "parameters.name as sensor_parameter_name, "
                                             "sensors_type.name as sensor_type_name "
                                             "FROM sensors "
                                             "LEFT JOIN sensors_parameters_links ON sensors_parameters_links.sensor_id=sensors.id "
                                             "LEFT JOIN parameters ON sensors_parameters_links.parameter_id=parameters.id "
                                             "LEFT JOIN sensors_type ON sensors.type=sensors_type.id  "
                                             "WHERE hardware_link_id = " + str(id))
        if result['error']:
            return result
        if len(result['result']) > 1:
            print('Error: Exist dublicate sensor link. Sensor sensor_id:' + id)
        result['result'] = result['result'][0]
        return result


    def get_actuator_id_param_from_db(self, id):
        '''
        :param id: Логический адрес нагрузки в контроллере
        :return: Dict данные о нагрузки из базы
        '''
        if type(id) != int:
            return {'result': '', 'error': True,
                    'error_message': 'get_actuator_id_param_from_db: Не указан адрес нагрузки для получения данных id != int'}
        result = self.dbconnect.ExecuteQuery("SELECT "
                                             "actuators.id as actuators_id, "
                                             "actuators.name as actuators_name, "
                                             "actuators.place_name as actuators_place_name, "
                                             "actuators_links.controller_hw_link as actuators_hw_link "
                                             "FROM actuators "
                                             "LEFT JOIN actuators_links ON actuators_links.actuators_id=actuators.id "
                                             "WHERE actuators_links.controller_hw_link=" + str(id))
        if result['error']:
            return result
        if len(result['result']) > 1:
            print('Error: Exist dublicate actuator link. Actuator id:' + id)
        if len(result['result']) < 1:
            return False  # Если пустой результат (нет данных)
        return result

    def UpdateSensorsHistory(self):
        '''
        Сохраниение данных с сенсоров в базе данных (в таблице истории значений)
        :return:
        '''
        # sensors, error, error_message = self.GetSensorsTemperatureIndex()
        result = self.GetSensorsTemperatureIndex()
        if result['error']:
            return result
        ''' Проверка на "Зависание" контроллера. Данное состояние проявляется отсутствием показаний на дисплее контроллера. Вместо температуры с датчиков
        отображаеются знаки "-"
        По запросу получения температуры через RS232 порт контроллер отдает последние считанные значения.
        Следовательно идентифицировать проблемную ситуацию будем по сравнению нескольких последовательных показаний,
        полученных от контроллера. Если несколько занчений были одинаковые, то считаем, что контроллер завис.
        '''
        if self.controller_is_freeze(result):
            print('ALERT: Controller is freeze!!!\n')
            #TODO реализовать отправку алертов в IM или на почту

        sensors = result['result']
        if config.mqtt_store:
            for key in sensors:
                # print key, " = ", sensors[key]
                link_id = str(sensors[key]['link_id'])
                sensor_value = str(sensors[key]['sensor_value'])
                sensor_addr = str(sensors[key]['addr'])
                if config.mqtt_store:
                    topic_1 = "home/thermostat/1/temperature/linkid/" + link_id
                    self.mqtt.publish(topic_1, sensor_value)
                    if config.debug_enable:
                        print('MQTT: Store data: ' + topic_1)
                    topic_2 = "home/thermostat/1/temperature/addr/" + sensor_addr
                    self.mqtt.publish(topic_2, sensor_value)
                    if config.debug_enable:
                        print('MQTT: Store data: ' + topic_2)
                if config.debug_enable:
                    print(
                    "INSERT INTO sensors_history (sensor_parameter_links_id, value_real, date, value_txt) VALUES ( " + link_id + ", " + sensor_value + ", NOW(),'')")
                result = self.dbconnect.ExecuteQuery(
                    "INSERT INTO sensors_history (sensor_parameter_links_id, value_real, date, value_txt) VALUES ( " + link_id + ", " + sensor_value + ", NOW(),'')")
        # return result
        return {'result': 'OK', 'error': False, 'error_message': ''}

    def get_sensor_hostory(self, link_id=0):
        '''
        Получение истории по заданному датчику
        :return:
        '''
        if not link_id:
            return False
        # DATE_FORMAT(sensors_history.date, "Y/m/d"),
        sql = "SELECT " \
              "sensors_history.date as s_date, " \
              "sensors_history.value_real as s_value_real " \
              "FROM " \
              "sensors_history " \
              "LEFT JOIN sensors ON sensors_history.sensor_parameter_links_id=sensors.id " \
              "LEFT JOIN sensors_parameters_links ON sensors_parameters_links.sensor_id=sensors.id " \
              "LEFT JOIN parameters ON sensors_parameters_links.parameter_id=parameters.id " \
              "WHERE " \
              "sensors_parameters_links.id=" + str(link_id) + " " \
                                                              "ORDER BY sensors_history.date DESC " \
                                                              "LIMIT " + str(config.sensor_graph_history_records)
        return self.dbconnect.ExecuteQuery(sql)

    def get_datetime(self):
        '''
        Получение времени от контроллера
        :return: Время полученное от контроллера
        '''
        datetime_raw = self._get_datetime_raw()
        return self._convert_datetime_raw(datetime_raw)

    def set_datetime(self, year, month, day, weekday, hours, minutes, seconds):
        '''

        :param year:
        :param month:
        :param day:
        :param weekday:
        :param hours:
        :param minutes:
        :param seconds:
        :return: True - если установка времени прошла успешно
        '''
        # TODO Написать функцию
        return {'result': 'OK', 'error': False, 'error_message': ''}

    def _get_datetime_raw(self):
        '''
        Получение даты и времени от контроллера в бинарном (сыром) виде
        :return:
        '''
        return self._do_command_get('c', 'c', 8)

    def _convert_datetime_raw(self, datetime_raw):
        '''
        Преобразование сырых данный от контроллера в список значений времени-даты
        :param datetime_raw:
        :return:
        '''
        seconds = ((ord(datetime_raw[0]) & 0b01110000) >> 4) * 10 + (ord(datetime_raw[0]) & 0b00001111)
        minutes = ((ord(datetime_raw[1]) & 0b01110000) >> 4) * 10 + (ord(datetime_raw[1]) & 0b00001111)
        hours = ((ord(datetime_raw[2]) & 0b00110000) >> 4) * 10 + (ord(datetime_raw[2]) & 0b00001111)
        weekday = ord(datetime_raw[3]) & 0b00000111
        day = ((ord(datetime_raw[4]) & 0b00110000) >> 4) * 10 + (ord(datetime_raw[4]) & 0b00001111)
        month = ((ord(datetime_raw[5]) & 0b00010000) >> 4) * 10 + (ord(datetime_raw[5]) & 0b00001111)
        year = 2000 + ((ord(datetime_raw[6]) & 0b11110000) >> 4) * 10 + (ord(datetime_raw[6]) & 0b00001111)
        return year, month, day, weekday, hours, minutes, seconds

    def _get_parts_of_digits(self, digit=0):
        '''
        :param digit: (0-99)
        :return: (d_h=<десятки(0..9>,d_l=<единицы(0..9)>)
        '''
        d_l = digit - digit // 10 * 10  # единицы
        d_h = (digit - d_l) / 10  # десятки
        return d_h, d_l

    def timedate_sync(self):
        '''
        Синхронизация времени и даты с сервером
        :return: True если синхронизация прошла успешно
        '''
        date_time = datetime.datetime.now()
        d_h, d_l = self._get_parts_of_digits(date_time.second)  # res[0]  # единицы секунд, res[1]  # десятки секунд
        result_raw_set = chr((d_h << 4) + d_l)
        d_h, d_l = self._get_parts_of_digits(date_time.minute)  # Минуты
        result_raw_set += chr((d_h << 4) + d_l)
        d_h, d_l = self._get_parts_of_digits(date_time.hour)  # Часы
        result_raw_set += chr((d_h << 4) + d_l)
        result_raw_set += chr(datetime.datetime.today().weekday() + 1)  # День недели
        d_h, d_l = self._get_parts_of_digits(date_time.day)  # Число месяца
        result_raw_set += chr((d_h << 4) + d_l)
        d_h, d_l = self._get_parts_of_digits(date_time.month)  # Месяц
        result_raw_set += chr((d_h << 4) + d_l)
        d_h, d_l = self._get_parts_of_digits(date_time.year - date_time.year // 100 * 100)  # Год
        result_raw_set += chr((d_h << 4) + d_l)
        result_raw_set += chr(0b0010000)
        if self._do_command_set('T', 'T', result_raw_set) != False:
            return {'result': 'OK', 'error': False, 'error_message': ''}
        return {'result': '', 'error': True, 'error_message': 'Не удалось синхронизировать время контроллера'}

    def get_program_raw(self):
        '''
        Получение программы в сыром виде
        :return:
        '''
        program = self._do_command_get('L', 'L', 32 * 27)
        if not program:
            return {'result': '', 'error': True,
                    'error_message': 'Программа от контроллера не получена или получена с ошибками'}
        # TODO Проверить. Возможно бинарный вид программы не ляжет сюда
        return {'result': program, 'error': False, 'error_message': ''}

    def get_program_json(self):
        '''
        Получение программы в виде JSON
        :return:
        '''
        res = self._do_command_get('L', 'L', 32 * 27)
        program = self.prg.decode_from_raw_tuple(res)
        if program['error']:
            return {'result': '', 'error': True,
                    'error_message': 'Программа от контроллера не получена или получена с ошибками. Ошибка: ' + program['error_message']}
        return {'result': program['result'], 'error': False, 'error_message': ''}

    def get_actuators_status_json(self):
        '''
        Получение старуса нагрузок в формате JSON
        :return:
        '''

        # TODO Перейти на использование функции GetActuatorsCurrent()
        result_raw = self._do_command_get('z', '', 2)
        if not result_raw:
            return {'result': '', 'error': True,
                    'error_message': 'Данные от контроллера не получены или получены с ошибками.'}

        actuators_status_raw = "{:08b}".format(ord(result_raw[1])) + "{:08b}".format(ord(result_raw[0]))
        actuators_status = actuators_status_raw[4:16]
        result = []
        for PinId in range(0, 12, 1):
            pin_out_state = {}
            res = self.get_actuator_id_param_from_db(PinId)
            pin_out_state['id'] = PinId
            pin_out_state['state'] = actuators_status[PinId]
            if res == False:
                pin_out_state['data'] = ''
            else:
                pin_out_state.update(res['result'][0])
            result.append(pin_out_state)
        return {'result': result, 'error': False, 'error_message': ''}




    def GetActuatorsCurrent(self):
        ''' Получение текущего статуса нагрузок
        :return: Словарь со статусами нагрузок

        # 4. ‘z’ Чтение реального состояния выходов в данный конкретный момент
        # Команда: 1 байт – ASCII-символ ‘z’
        # Ответ: 2 байтное число, каждый бит которого соответствует состоянию выхода:
        # 11 бит сопоставлен 1 выходу,
        # 10 бит – 2 выходу
        # и т.д. до 0 бита, который соответствует 12 выходу
        '''
        result_raw = self._do_command_get('z', '', 2)
        if not result_raw:
            return {'result': '', 'error': True,
                    'error_message': 'Данные от контроллера не получены или получены с ошибками.'}

        actuators_status_raw = "{:08b}".format(ord(result_raw[1])) + "{:08b}".format(ord(result_raw[0]))
        actuators_status = actuators_status_raw[4:16]
        result = []
        for PinId in range(0, 12, 1):
            result[PinId] = actuators_status[PinId]
        return {'result': result, 'error': False, 'error_message': ''}


    def controller_is_freeze(self, current_sensor_temperature):
        ''' Проверка на "зависание" контроллера

        :param current_sensor_temperature: dict текущие значения температуры от датчиков
        :return:
        '''
        self.controller_fr_struct.add(current_sensor_temperature)
        return self.controller_fr_struct.is_freeze()
