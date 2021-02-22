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
print ' --- START ---'

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
        # 1. ‘t’ Чтение значений температуры
        # Команда: 1 байт – ASCII-символ ‘t’
        # Ответ: 1 байт количество температурных датчиков (32), далее передаются значения температуры всех 32 датчиков.
        # Формат числа int(16-битное знаковое целое число со значением температуры, умноженное на 100).
        ########################################################################
        print ' --- 1.Get temperature(sensors) ---'
        ser.flush() # Не удалять!!!
        result_raw = str("")
        read_loop_counter = 0
        result_true = False
        while result_true == False and read_loop_counter < read_loop_max:
            ser.write("t")
            while int(ord(ser.read(1))) != 32:
                pass
            result_raw = ser.read(64)
            # Если получено не 64 байта, то получаем ошибку
            if len(result_raw) != 64:
                result_true = False
                read_loop_counter = read_loop_counter + 1
            else:
                result_true = True

        if result_true == True:
            print(' --- read ' + str(len(result_raw)) + ' bytes')
            for sensor_id in range(0, 63, 2):
                sign_temperature_raw = struct.unpack('<h', result_raw[sensor_id] + result_raw[sensor_id+1])
                sign_temperature = (float(sign_temperature_raw[0]))/100
                print('t(' + str(sensor_id/2) + ')=' + '{0:4.2f}'.format(sign_temperature) + ' ˚C')
        else:
            print("Error read current temperature from controller")



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
        print ' --- 4.Real status on outputs ---'
        ser.flush()
        ser.write("z")
        result_raw = ser.read(2)
        print("outputs state (BIN) >> " + '{0:08b}'.format(ord(result_raw[1])) + '{0:08b}'.format(ord(result_raw[0])))
        print("After BIN mask")
        test = ord(result_raw[1]) + ord(result_raw[0]) << 8
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

        ########################################################################
        # 5. ‘b’ Чтение уровня заряда батареи часов реального времени
        # Команда: 1 байт – ASCII-символ ‘b’
        # Ответ: 2 байтное слово соответствующее представлению числа от 0 до 1024,
        # что соответствует напряжению соответственно от 0 до 5В
        ########################################################################
        print ' --- 5.Battary voltage ---'
        ser.flush()
        ser.write("b")
        result_raw = ser.read(2)
        result_txt = str('{0:4.2f}'.format(float((float(ord(result_raw[0])) + float(ord(result_raw[1]))*256)*5/1024)))
        print(result_txt + 'V')

        ########################################################################
        # 6. ‘V’ Чтение версии ПО микроконтроллера
        # Команда: 1 байт – ASCII-символ ‘V’
        # Ответ: символ ‘V’,далее 1 байт – число, представляющее длину строки текста,
        # который следует после (в конце строки нет флага окончания строки 00h)
        ########################################################################
        print ' --- 6.Current version firmware ---'
        ser.flush()
        ser.write("V")
        while ser.read(1) != "V":
            pass
        ver_str_len = ser.read(1)
        ver_str = ser.read(ord(ver_str_len))
        print("Version: " + ver_str)

        ########################################################################
        # 8. ‘c’ Чтение времени
        # Команда: 1 байт – ASCII-символ ‘с’
        # Ответ: 1 байт ’эхо” символ ‘с’, следуют данные календаря по структуре описанной нижу. Суммарно 8 байт.
        # Описание структуры:
        # struct struct_clock{
        # // байт №1
        # unsigned char seconds:4; / /секунды (4 бита)
        # unsigned char ten_seconds:3; // десятки секунд (3 бита)
        # unsigned char ch:1; // всегда = 0 (1 бит)
        # // байт №2
        # unsigned char minutes:4; // минуты
        # unsigned char ten_minutes:3; // десятки минут
        # unsigned char reserved_0:1;
        # // байт №3
        # unsigned char hours:4; // часы
        # unsigned char ten_hours:2;// десятки часа
        # unsigned char AMPM_24_mode:1; // всегда =0
        # unsigned char reserved_1:1; // зарезервирован
        # // байт №4
        # unsigned char day:3; // День недели (1-7)
        # unsigned char reserved_2:5;
        # // байт №5
        # unsigned char date:4; // число (1-31)
        # unsigned char ten_date:2; // число (десятки)
        # unsigned char reserved_3:2;
        # // байт №6
        # unsigned char month:4; // месяц (1-12)
        # unsigned char ten_month:1; // месяц(десятки)
        # unsigned char reserved_4:3;
        # // байт №7
        # unsigned char year:4; // год от 0 до 99
        # unsigned char ten_year:4; // десятки года
        # // байт №8
        # unsigned char RS:2; // всегда =0
        # unsigned char reserved_5:2;
        # unsigned char SQWE:1; // всегда =1
        # unsigned char reserved_6:2;
        # unsigned char OUT:1; // всегда =1
        # };
        ########################################################################

        def get_datetime_raw(ser):
            '''
            Получение даты и времени от контроллера в бинарном (сыром) виде
            :return:
            '''
            ser.flush()
            ser.write("c")
            # "c"
            while ser.read(1) != "c":
                pass
            result_raw = ser.read(8)
            return result_raw


        def convert_datetime_raw(datetime_raw):
            '''

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


        def get_datetime(ser):
            '''
            Получение даты и времени от контроллера
            :return:
            '''
            datetime_raw = get_datetime_raw(ser)
            return convert_datetime_raw(datetime_raw)



        print ' --- 8.0.Get time (new method) --- '
        year, month, day, weekday, hours, minutes, seconds = get_datetime(ser)
        print('date: ' + str(year) + '-' + "{:0>2d}".format(month) + '-' + "{:0>2d}".format(day) + ' day:' + str(
            weekday) + ' ' + "{:0>2d}".format(hours) + ":" + "{:0>2d}".format(minutes) + ":" + "{:0>2d}".format(seconds))


        print ' --- 8.Get time --- '
        ser.flush()
        ser.write("c")
        # "c"
        while ser.read(1) != "c":
            pass
        result_raw = ser.read(8)

        seconds = ((ord(result_raw[0]) & 0b01110000) >> 4) * 10 + (ord(result_raw[0]) & 0b00001111)
        minutes = ((ord(result_raw[1]) & 0b01110000) >> 4) * 10 + (ord(result_raw[1]) & 0b00001111)
        hours = ((ord(result_raw[2]) & 0b00110000) >> 4) * 10 + (ord(result_raw[2]) & 0b00001111)
        day = ord(result_raw[3]) & 0b00000111
        date = ((ord(result_raw[4]) & 0b00110000) >> 4) * 10 + (ord(result_raw[4]) & 0b00001111)
        month = ((ord(result_raw[5]) & 0b00010000) >> 4) * 10 + (ord(result_raw[5]) & 0b00001111)
        year = 2000 + ((ord(result_raw[6]) & 0b11110000) >> 4) * 10 + (ord(result_raw[6]) & 0b00001111)


        print('date: '+str(year)+'-'+"{:0>2d}".format(month)+'-'+"{:0>2d}".format(date)+' day:'+str(day)+' '+"{:0>2d}".format(hours)+":"+"{:0>2d}".format(minutes)+":"+"{:0>2d}".format(seconds))

        ########################################################################
        # 7. ‘T’ Запись времени
        # Команда: 1 байт – ASCII-символ ‘T’
        # Ответ: 1 байт ’эхо” символ ‘T’.
        # Команда: передаются данные календаря по указанной структуре. Суммарно 8 байт.
        ########################################################################
        print ' --- 7.Set date/time ---'

        # :return: (d_h=<десятки(0..9>,d_l=<единицы(0..9)>)
        def get_parts_of_digits(digit=0):
            d_l = digit - digit // 10 * 10  # единицы
            d_h = (digit - d_l) / 10  # десятки
            return d_h, d_l

        date_time = datetime.datetime.now()

        d_h, d_l = get_parts_of_digits(date_time.second)  # res[0]  # единицы секунд, res[1]  # десятки секунд
        result_raw_set = chr((d_h << 4) + d_l)

        d_h, d_l = get_parts_of_digits(date_time.minute)
        result_raw_set += chr((d_h << 4) + d_l)

        d_h, d_l = get_parts_of_digits(date_time.hour)
        result_raw_set += chr((d_h << 4) + d_l)

        result_raw_set += chr(datetime.datetime.today().weekday() + 1)

        d_h, d_l = get_parts_of_digits(date_time.day)
        result_raw_set += chr((d_h << 4) + d_l)

        d_h, d_l = get_parts_of_digits(date_time.month)
        result_raw_set += chr((d_h << 4) + d_l)

        d_h, d_l = get_parts_of_digits(date_time.year - date_time.year//100*100)
        result_raw_set += chr((d_h << 4) + d_l)

        result_raw_set += chr(0b0010000)


        # Проверим правильность сформированного пакета
        seconds = ((ord(result_raw_set[0]) & 0b01110000) >> 4) * 10 + (ord(result_raw_set[0]) & 0b00001111)
        minutes = ((ord(result_raw_set[1]) & 0b01110000) >> 4) * 10 + (ord(result_raw_set[1]) & 0b00001111)
        hours = ((ord(result_raw_set[2]) & 0b00110000) >> 4) * 10 + (ord(result_raw_set[2]) & 0b00001111)
        day = ord(result_raw_set[3]) & 0b00000111
        date = ((ord(result_raw_set[4]) & 0b00110000) >> 4) * 10 + (ord(result_raw_set[4]) & 0b00001111)
        month = ((ord(result_raw_set[5]) & 0b00010000) >> 4) * 10 + (ord(result_raw_set[5]) & 0b00001111)
        year = 2000 + ((ord(result_raw_set[6]) & 0b11110000) >> 4) * 10 + (ord(result_raw_set[6]) & 0b00001111)
        print '  - test Set date/time :'
        print('date: '+str(year)+'-'+"{:0>2d}".format(month)+'-'+"{:0>2d}".format(date)+' day:'+str(day)+' '+"{:0>2d}".format(hours)+":"+"{:0>2d}".format(minutes)+":"+"{:0>2d}".format(seconds))
        ser.write("T")  # "T"
        while ser.read(1) != "T":
            pass
        ser.write(result_raw_set)
        #exit()


        ########################################################################
        # 9. ‘L’ Считывание программы управления в компьютер
        # Команда: 1 байт – ASCII-символ ‘L’
        # Ответ: 1 байт “’эхо” символ ‘L’, далее 832 байта данных. Передаются 32 записи,
        # каждая из которых соответствует нижеописанной структуре.
        # Каждая структура занимает 27 байт, поэтому, суммарно 27 * 32 = 864 байта
        # Описание структуры:
        #   struct DataToORFromPC{
        #       unsigned char time_on_h; // время старта час 0-23
        #       unsigned char time_on_m; // время старта минута 0-59
        #       unsigned char time_on_s; // время старта секунда 0-59
        #       unsigned char time_off_h; // время остановки час 0-23
        #       unsigned char time_off_m; // время остановки минута 0-59
        #       unsigned char time_off_s; // время остановки секунда 0-59
        #       unsigned char time_on_day; // число старта 1-31
        #       unsigned char time_off_day; // число остановки 1-31
        #       unsigned char time_on_month; // месяц старта от 1 до 12
        #       unsigned char time_off_month; // месяц остановки от 1 до 12
        #       unsigned char time_on_year; // ГОД СТАРТА от 0 до 99 (соответствует от 2000 до 2099)
        #       unsigned char time_off_year; // ГОД ОСТАНОВКИ от 0 до 99 (соответствует от 2000 до 2099)
        #       unsigned char time_load; // номер нагрузки от 0 до 7
        #       unsigned char time_loadsensor; // логический номер датчика уменьшенный на 1 , с которым работает данная программа
        #       unsigned short time_min; // минимум, для датчиков температуры это от -5500 до +12500 (-55 до 125град),
        #                                   для АЦП это от 0 до 1023(цифровые показания АЦП);
        #                                   при сравнении двух датчиков - номер второго датчика от 0 до 31
        #       unsigned short time_max; // максимум, для датчиков температуры это от -5500 до +12500 (-55 до 125град),
        #                                   для АЦП это от 0 до 1023(цифровые показания АЦП)
        #       unsigned char time_mode ; // режим 0=нагрев, 1= охлаждение, 2= будильник, 3=по таймеру
        #       unsigned char time_eze; //отрабатывать по дням=1, по дням недели=2, по месяцам=3, без периода=0
        #       unsigned long time_ezedata; // 32 бита соответствующие выбранной периодичности
        #       unsigned char time_bud; // служебный (считать и записать в то же состояние)
        #       unsigned char enable; // разрешение работы данного канала
        #       unsigned char sensortype; // Бит 3: 1– сравнение двух датчиков, если 0, то проверить бит 0:
        #                                   (бит 0): 0 – DS18B20, 1 – аналоговый вход;
        #                                   бит 1:– Закон ИЛИ/И.
        #   };
        ########################################################################
        print ' --- 9.Get program ---'
        result_data = []
        dict_time_mode = {0:"Heating",1:"Cooling",2:"Buzzer",3:"Timer"}
        dict_time_eze =  {0:"No period",1:"By day",2:"By week days",3:"By month"}
        dict_sensortype =  {0:"DS18B20",1:"Analog",2:"",3:""}
        dict_enable = {0:"Off",1:"On"}
        ser.flush()
        ser.write("L")  # "L"
        while ser.read(1) != "L":
            pass

        for programm_id in range(0, 32, 1):
            result_get = ser.read(27)
            result_data.append(str(result_get))
            # Вывод кода программы в бинарном виде
            #print('{:0>2d}'.format(programm_id) + ': ' + str(result_get.encode("HEX")))

            time_on_h =         ord(result_get[0])
            time_on_m =         ord(result_get[1])
            time_on_s =         ord(result_get[2])
            time_off_h =        ord(result_get[3])
            time_off_m =        ord(result_get[4])
            time_off_s =        ord(result_get[5])
            time_on_day =       ord(result_get[6])
            time_off_day =      ord(result_get[7])
            time_on_month =     ord(result_get[8])
            time_off_month =    ord(result_get[9])
            time_on_year =      ord(result_get[10])
            time_off_year =     ord(result_get[11])
            time_load =         ord(result_get[12])
            time_loadsensor =   ord(result_get[13])
            # TODO проверить на правильность отображения температуры при отрицательных значениях температуры в программе
            if (ord(result_get[14]) != 0 and ord(result_get[15]) != 0):
                time_min = float(ord(result_get[14]) + (ord(result_get[15]) << 8))*0.01
            else:
                time_min = 0
            if (ord(result_get[16]) != 0 and ord(result_get[17]) != 0):
                time_max = float(ord(result_get[16]) + (ord(result_get[17]) << 8))*0.01
            else:
                time_max = 0
            time_mode =         ord(result_get[18])
            time_eze =          ord(result_get[19])
            time_ezedata =      ord(result_get[23]) + \
                                ord(result_get[22]) << 8 + \
                                ord(result_get[21]) << 16 + \
                                ord(result_get[20]) << 24
            time_bud =          ord(result_get[24])
            enable =            ord(result_get[25])
            sensortype =        ord(result_get[26])

            mode_txt = dict_time_mode.get(time_mode)
            enable_txt = dict_enable.get(enable)
            sensortype_txt = dict_sensortype.get(sensortype)

            print('Program(' + str(programm_id) + ') '+enable_txt+' '+mode_txt+' '+sensortype_txt+' Start: ' \
                  + str(2000+time_on_year) + '.' + '{:0>2d}'.format(time_on_month) + '.' + '{:0>2d}'.format(time_on_day) + ' ' \
                  + '{:0>2d}'.format(time_on_h) + ':' + '{:0>2d}'.format(time_on_m) + ':' + '{:0>2d}'.format(time_on_s) \
                  + ' Stop: ' \
                  + str(2000+time_off_year) + '.' + '{:0>2d}'.format(time_off_month) + '.' + '{:0>2d}'.format(time_off_day) + ' ' \
                  + '{:0>2d}'.format(time_off_h) + ':' + '{:0>2d}'.format(time_off_m) + ':' + '{:0>2d}'.format(time_off_s) \
                  + ' L(' + str(time_load) + ')' \
                  + ' Sensor(' + str(time_loadsensor+1) + ')' \
                  + ' t ' + str(time_min) \
                  + '...' + str(time_max) + ' ˚C' \
                  )

        ########################################################################
        # 11. ‘D’ Считывание серийных номеров зарегистрированных датчиков Dallas
        # Команда: 1 байт – ASCII-символ ‘D’
        # Ответ: 1 байт «эхо» - символ ‘D’,
        # после передается 32 поля серийных номеров DS18B20 по 8 байт (суммарно 256 байт),
        # если датчик не зарегистрирован на центральном блоке – то получить его серийный номер не получится
        ########################################################################
        print ' --- 11.Get sensor from line ---'
        ser.flush()
        ser.write("D")
        # "D"
        while ser.read(1) != "D":
            pass
        result_data = []
        # Content in graphical format
        for sensor_id in range(0, 31, 1):
            result_raw = ser.read(8)
            addr_string = ""
            addr_byte = ""
            sensor_is_exist = False
            for ind in range (0, len(result_raw), 1):
                addr_byte = "{:02x}".format(int(ord(result_raw[ind])))
                addr_string += ":" + str(addr_byte)
                if addr_byte != "00":
                    sensor_is_exist = True
            if sensor_is_exist:
                result_data.append(addr_string)

        for sensor_id in range(0, len(result_data), 1):
            print(result_data[sensor_id])

        ########################################################################
        # 20. ‘S’ Считывание содержимого дисплея
        # Команда: 1 байт – ASCII-символ ‘S’
        # Ответ: 1 байт «эхо» - символ ‘S’
        # 64 байта – содержимое графической памяти
        # 16 байт – верхняя строка
        # 16 байт – нижняя строка
        # Итого 96 байт. Смотреть таблицу символов дисплея!
        ########################################################################
        print ' --- 20.Display content ---'
        ser.flush()
        ser.write("S")
        # "S"
        while ser.read(1) != "S":
            pass
        result_raw = ser.read(64+16+16)
        # Content in graphical format
        result_raw_content_graph64 = result_raw[0:63]
        # Content in text format (up string)
        result_raw_content_txt1 = result_raw[63:63+16]
        # Content in text format (down string)
        result_raw_content_txt2 = result_raw[63+16:63+16+16]
        print(str(result_raw_content_txt1))
        print(str(result_raw_content_txt2))




    except  Exception,  e1:
        print "error communicating...: " + str(e1)

    ser.close()
else:
    print "cannot open serial port "
