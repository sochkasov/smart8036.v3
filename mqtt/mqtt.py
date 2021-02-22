# coding=utf8

import paho.mqtt.client as mqtt
import config


class MQTT(object):

    # Делаем Singletone
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(MQTT, cls).__new__(cls)
        return cls.instance


    def __init__(self):
        # TODO Вынести MQTT настройки в конфиг
        self.mqtt_client = mqtt.Client(client_id="thermostat_8036_#1")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(config.mqtt_host, config.mqtt_port, config.mqtt_keepalive)
        #self.mqtt_client.loop_forever()  # TODO вынести в отдельный тред

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        #client.subscribe("$SYS/#")

    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))

    def publish(self, topic="", msg=None):
        self.mqtt_client.publish(topic, msg)
        print ("MQTT publish topic=%s, msg=%s)" % (topic, msg))
