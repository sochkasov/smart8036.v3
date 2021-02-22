import threading
import atexit
from flask import Flask

POOL_TIME = 5 #Seconds

# Переменные, которые доступны ото всюду (variables that are accessible from anywhere)
commonDataStruct = {}
# lock для контроля доступа к переменной (lock to control access to variable)
dataLock = threading.Lock()
# указатель треда (thread handler)
yourThread = threading.Thread()

def create_app():
    app = Flask(__name__)

    def interrupt():
        global yourThread
        yourThread.cancel()

    def doStuff():
        global commonDataStruct
        global yourThread
        with datalock:
        #
        # Do your stuff with commonDataStruct Here

        # Set the next thread to happen
        yourThread = threading.Timer(POOL_TIME, doStuff, ())
        yourThread.start()

    def doStuffStart():
        # Инициализация вашего треда (Do initialisation stuff here)
        global yourThread
        # Создание вашего треда (Create your thread)
        yourThread = threading.Timer(POOL_TIME, doStuff, ())
        yourThread.start()

    # Инициирование (Initiate)
    doStuffStart()
    # When you kill Flask (SIGTERM), clear the trigger for the next thread
    atexit.register(interrupt)
    return app

app = create_app()
