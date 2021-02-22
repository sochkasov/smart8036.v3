# coding=utf8

import MySQLdb as mdb
import config


class Database(object):
    connection = None

    # Делаем Singletone
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Database, cls).__new__(cls)
        return cls.instance


    def __init__(self):
        return self.get_connection()
        return None


    def get_connection(self):
        #global connection
        if not self.connection:
            try:
                self.connection = mdb.connect(host=config.mysql_host, user=config.mysql_user, passwd=config.mysql_password, db=config.mysql_db)
                #self.connection.set_character_set('cp1251')
                self.connection.set_character_set('utf8')
                print "OK: Connect to MySQL server is sucсessful"
            except Exception, e:
                print "ERROR: Connection to MySQL server is failed: " + str(e)
                return None
        return None


    def close_connection(self):
        self.connection.close()


    def ExecuteQuery(self,query):
        #error_flag = False
        try:
            cursor = self.connection.cursor()
            cur = self.connection.cursor(mdb.cursors.DictCursor)
            if config.debug_sql_enable:
                print("SQL: " + query)
            cur.execute(query)
            result = cur.fetchall()
        except:
            return {'result': {}, 'error': True, 'error_message': "MySQL Error"}
        else:
            return {'result': result, 'error': False, 'error_message': ''}
