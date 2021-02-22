# coding=utf8

import os
from flask import Flask, jsonify, send_file
from flask import request
from flask_jsonpify import jsonify  # для JSONP
from flask.json import JSONEncoder

import ujson
from api_utils import ResponsiveFlask
from HeatController.Controller8036 import *
import config
import datetime
import calendar


class CustomJSONEncoder(JSONEncoder):
    '''
    Преопределение метода для изменения преобразования даты-времени в нужный формат
    '''
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return str(obj)
        return JSONEncoder.default(self, obj)


class ServerAPI(object):

    def __init__(self):
        self.DEBUG = False
        print "ServerAPI server\n"
        self.dbconnect = db.Database()
        self.ctl8036 = Controller8036()
        #self.app = ResponsiveFlask(__name__)
        self.app = Flask(__name__)
        self.app.json_encoder = CustomJSONEncoder
        self.app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
        return None


    def json_output(self, *args, **kwargs):
        """
        Создание JSON строки из data. Производится контроль ошибок по флагу error
        Если есть ошибка, то будет сформировано сообщение из error_message
        :param data:
        :param error:
        :param error_message:
        :return:
        """
        if not kwargs['error']:
            # return jsonify(kwargs['result'])
            return jsonify({"result": kwargs['result'], "error": False, "error_message": kwargs['error_message']}), 200
        else:
            return jsonify({"error": True, "error_message": kwargs['error_message']}), 404


    def start(self):
        @self.app.route('/')
        def index():
            return jsonify(api_version=1,
                           user='user1',
                           datatime=str(datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')),
                           date=str(datetime.datetime.now().strftime('%d-%m-%Y')),
                           time=str(datetime.datetime.now().strftime('%H:%M:%S'))
                           )

        @self.app.route('/help')
        def get_help():
            result = '''<h2>API methods</h2>
                        <ul>
                           <li>/get/temp/ - get temperature online on JSON format</li>
                           <li>/get/tempraw/ - get temperature online on raw format</li>
                        </ul>'''
            return {'message': result}

        @self.app.route('/get/temp/')
        def get_temp():
            return self.json_output(**self.ctl8036.GetSensorsTemperature())

        @self.app.route('/get/temp/history/<int:sensor_link_id>')
        def get_temp_history(sensor_link_id):
            return self.json_output(**self.ctl8036.get_sensor_hostory(sensor_link_id))

        @self.app.route('/get/tempraw/')
        def get_tempraw():
            return self.json_output(**self.ctl8036.GetTemperatureCurrent())

        @self.app.route('/set/timesync/')
        def set_temesync():
            return self.json_output(**self.ctl8036.timedate_sync())

        @self.app.route('/get/program_raw/')
        def get_programm_raw():
            return self.json_output(**self.ctl8036.get_program_raw())

        @self.app.route('/get/program_json/')
        def get_programm_json():
            return self.json_output(**self.ctl8036.get_program_json())

        @self.app.route('/get/actuator_status/')
        def get_actuators_status_json():
            return self.json_output(**self.ctl8036.get_actuators_status_json())

        @self.app.route('/get/test/')
        def get_test():
            return jsonify({'now': datetime.datetime.now()})

        @self.app.route('/favicon.ico')
        def favicon():
            #  mimetype='image/vnd.microsoft.icon'
            #return      "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAIFQTFRFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA////basLdwAAACp0Uk5TAAgEHQMYbYWESXFmcywiYnuGamt0QyafblMHb1kLCmg8AjZ2I2EQciFgf8bHLwAAAAFiS0dEKlO+1J4AAAAJcEhZcwAAAEgAAABIAEbJaz4AAACLSURBVBgZBcELQoJQEADAkeengJYiIrXC76Lc/4LNAAAAWK0AqEpZb7bbDYCye3mtm6Z9A4ju/aPv+8/haw2M3/v6cDwe6p/fP5hO++F84XIe+mbCdL2NwHi7TnDvALo7iDRnZs4yQKR4PJ+PkAEixcISMkCkSDJkgLJb2iTbZVdAVSJm5ohSAQDgH8c2Ci4yRvReAAAAJXRFWHRkYXRlOmNyZWF0ZQAyMDE2LTA5LTE2VDA4OjI4OjI3KzAwOjAwlMYpngAAACV0RVh0ZGF0ZTptb2RpZnkAMjAxNi0wOS0xNlQwODoyODoyNyswMDowMOWbkSIAAABGdEVYdHNvZnR3YXJlAEltYWdlTWFnaWNrIDYuNy44LTkgMjAxNC0wNS0xMiBRMTYgaHR0cDovL3d3dy5pbWFnZW1hZ2ljay5vcmfchu0AAAAAGHRFWHRUaHVtYjo6RG9jdW1lbnQ6OlBhZ2VzADGn/7svAAAAGHRFWHRUaHVtYjo6SW1hZ2U6OmhlaWdodAAxOTIPAHKFAAAAF3RFWHRUaHVtYjo6SW1hZ2U6OldpZHRoADE5MtOsIQgAAAAZdEVYdFRodW1iOjpNaW1ldHlwZQBpbWFnZS9wbmc/slZOAAAAF3RFWHRUaHVtYjo6TVRpbWUAMTQ3NDAxNDUwN/jek0AAAAAPdEVYdFRodW1iOjpTaXplADBCQpSiPuwAAABWdEVYdFRodW1iOjpVUkkAZmlsZTovLy9tbnRsb2cvZmF2aWNvbnMvMjAxNi0wOS0xNi9jY2EzODcyMTQ3Mjc5YTVmYTVmMDVlNDJiYzA4ZDI0NC5pY28ucG5nM8/R6gAAAABJRU5ErkJggg==", 200, {'Content-Type': 'image/vnd.microsoft.icon'}
            #data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAIFQTFRFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA////basLdwAAACp0Uk5TAAgEHQMYbYWESXFmcywiYnuGamt0QyafblMHb1kLCmg8AjZ2I2EQciFgf8bHLwAAAAFiS0dEKlO+1J4AAAAJcEhZcwAAAEgAAABIAEbJaz4AAACLSURBVBgZBcELQoJQEADAkeengJYiIrXC76Lc/4LNAAAAWK0AqEpZb7bbDYCye3mtm6Z9A4ju/aPv+8/haw2M3/v6cDwe6p/fP5hO++F84XIe+mbCdL2NwHi7TnDvALo7iDRnZs4yQKR4PJ+PkAEixcISMkCkSDJkgLJb2iTbZVdAVSJm5ohSAQDgH8c2Ci4yRvReAAAAJXRFWHRkYXRlOmNyZWF0ZQAyMDE2LTA5LTE2VDA4OjI4OjI3KzAwOjAwlMYpngAAACV0RVh0ZGF0ZTptb2RpZnkAMjAxNi0wOS0xNlQwODoyODoyNyswMDowMOWbkSIAAABGdEVYdHNvZnR3YXJlAEltYWdlTWFnaWNrIDYuNy44LTkgMjAxNC0wNS0xMiBRMTYgaHR0cDovL3d3dy5pbWFnZW1hZ2ljay5vcmfchu0AAAAAGHRFWHRUaHVtYjo6RG9jdW1lbnQ6OlBhZ2VzADGn/7svAAAAGHRFWHRUaHVtYjo6SW1hZ2U6OmhlaWdodAAxOTIPAHKFAAAAF3RFWHRUaHVtYjo6SW1hZ2U6OldpZHRoADE5MtOsIQgAAAAZdEVYdFRodW1iOjpNaW1ldHlwZQBpbWFnZS9wbmc/slZOAAAAF3RFWHRUaHVtYjo6TVRpbWUAMTQ3NDAxNDUwN/jek0AAAAAPdEVYdFRodW1iOjpTaXplADBCQpSiPuwAAABWdEVYdFRodW1iOjpVUkkAZmlsZTovLy9tbnRsb2cvZmF2aWNvbnMvMjAxNi0wOS0xNi9jY2EzODcyMTQ3Mjc5YTVmYTVmMDVlNDJiYzA4ZDI0NC5pY28ucG5nM8/R6gAAAABJRU5ErkJggg=="
            #data = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAIFQTFRFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA////basLdwAAACp0Uk5TAAgEHQMYbYWESXFmcywiYnuGamt0QyafblMHb1kLCmg8AjZ2I2EQciFgf8bHLwAAAAFiS0dEKlO+1J4AAAAJcEhZcwAAAEgAAABIAEbJaz4AAACLSURBVBgZBcELQoJQEADAkeengJYiIrXC76Lc/4LNAAAAWK0AqEpZb7bbDYCye3mtm6Z9A4ju/aPv+8/haw2M3/v6cDwe6p/fP5hO++F84XIe+mbCdL2NwHi7TnDvALo7iDRnZs4yQKR4PJ+PkAEixcISMkCkSDJkgLJb2iTbZVdAVSJm5ohSAQDgH8c2Ci4yRvReAAAAJXRFWHRkYXRlOmNyZWF0ZQAyMDE2LTA5LTE2VDA4OjI4OjI3KzAwOjAwlMYpngAAACV0RVh0ZGF0ZTptb2RpZnkAMjAxNi0wOS0xNlQwODoyODoyNyswMDowMOWbkSIAAABGdEVYdHNvZnR3YXJlAEltYWdlTWFnaWNrIDYuNy44LTkgMjAxNC0wNS0xMiBRMTYgaHR0cDovL3d3dy5pbWFnZW1hZ2ljay5vcmfchu0AAAAAGHRFWHRUaHVtYjo6RG9jdW1lbnQ6OlBhZ2VzADGn/7svAAAAGHRFWHRUaHVtYjo6SW1hZ2U6OmhlaWdodAAxOTIPAHKFAAAAF3RFWHRUaHVtYjo6SW1hZ2U6OldpZHRoADE5MtOsIQgAAAAZdEVYdFRodW1iOjpNaW1ldHlwZQBpbWFnZS9wbmc/slZOAAAAF3RFWHRUaHVtYjo6TVRpbWUAMTQ3NDAxNDUwN/jek0AAAAAPdEVYdFRodW1iOjpTaXplADBCQpSiPuwAAABWdEVYdFRodW1iOjpVUkkAZmlsZTovLy9tbnRsb2cvZmF2aWNvbnMvMjAxNi0wOS0xNi9jY2EzODcyMTQ3Mjc5YTVmYTVmMDVlNDJiYzA4ZDI0NC5pY28ucG5nM8/R6gAAAABJRU5ErkJggg=='
            #return send_file(data, mimetype='image/vnd.microsoft.icon',)
            #return Response(stream_with_context(data), mimetype='image/vnd.microsoft.icon')
            #return send_from_directory(os.path.join(self.app.root_path, 'static'),'htdocs/favicon/home-outline.ico/favicon.ico',mimetype='image/vnd.microsoft.icon')
            return send_file('/root/8036/htdocs/favicon/home-outline.ico/favicon.ico', mimetype='image/vnd.microsoft.icon', )


        @self.app.errorhandler(404)
        def page_not_found(error):
            return {'error': 'This API method does not exist'}, 404

        # Running web server
        #if __name__ == '__main__':
        if __name__ == 'ServerAPI.ServerAPI':
            print "API server listen on port 5000 ..."
            # global DEBUG
            # if self.DEBUG:
            #    self.app.debug = True
            #self.app.run(host=config.http_listen_ip, port=config.http_listen_port, debug=config.debug_enable, threaded=False)
            self.app.run(host=config.http_listen_ip, port=config.http_listen_port, debug=False, threaded=False)

    def stop(self):
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
