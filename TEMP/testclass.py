import serial
class Controller8036(object):
    #import serial
    def __int__(self):
        # Подключаемся к контроллеру
        self.ser = serial.Serial(object)
        self.ser.port = "/dev/ttyS0"
        self.ser.baudrate = 9600
        self.ser.bytesize = 8  #number of bits per bytes
        self.ser.stopbits = 2  #number of stop bits
        self.ser.timeout = 2
        self.ser.parity = serial.PARITY_NONE  #set parity check: no parity
        self.ser.xonxoff = False  #disable software flow control
        self.ser.rtscts = False  #disable hardware (RTS/CTS) flow control
        self.ser.dsrdtr = False  #disable hardware (DSR/DTR) flow control
        self.ser.writeTimeout = 1  #timeout for write

        try:
            self.ser.open()
            return True
        except Exception, e:
            print "error open serial port: " + str(e)
            return False

    def testConnection(self):
        # Проверка того, что контроллер отвечает, если не отвечает вываливаться с ошибкой (генерировать исключение)
        self.ser.flush()
        self.ser.write("b")
        result_raw = self.ser.read(2)
        if len(result_raw)!=2:
            return False
        return True
