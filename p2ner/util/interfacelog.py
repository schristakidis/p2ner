#   Copyright 2012 Loris Corazza, Sakis Christakidis
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
        
import sqlite3 as lite
from p2ner.util.utilities import get_user_data_dir
from p2ner.abstract.interface import Interface
import os

class DatabaseLog(Interface):
    def initInterface(self,server=False):
        if server:
            self.defaultIp='server'
        else:
            self.defaultIp='peer'
        userdatadir = get_user_data_dir()
        if not os.path.isdir(userdatadir):
            os.mkdir(userdatadir)
        if not os.path.isdir(os.path.join(userdatadir, "log")):
            os.mkdir(os.path.join(userdatadir, "log"))
        self.db= os.path.join(get_user_data_dir(), "log",'p2ner.db')
        print self.db
        self.con=lite.connect(self.db)
        self.id=0
        self.lastId=0
        with self.con:
            cur =self.con.cursor()   
            cur.execute('DROP TABLE IF EXISTS log')
            cur.execute('CREATE TABLE log(id INTEGER PRIMARY KEY AUTOINCREMENT, ip Text, port INTEGER, level TEXT, log TEXT, time TEXT, epoch REAL, msecs REAL,module TEXT, func TEXT, lineno INTEGER, msg TEXT) ')

        
    def addRecord(self,record):
        try:
            ip=self.root.netChecker.externalIp
            port=self.root.netChecker.controlPort
        except:
            ip=self.defaultIp
            port=0
        args=(ip,port,record.levelname,record.name,record.asctime,record.created,record.msecs,record.module,record.funcName,record.lineno,record.getMessage())
        with self.con:
            cur =self.con.cursor()   
            cur.execute('INSERT INTO log(ip,port,level,log,time,epoch,msecs,module,func,lineno,msg) VALUES(?,?,?,?,?,?,?,?,?,?,?)',args)
            self.lastId=cur.lastrowid
        
        
    def getRecords(self):
        if self.id==self.lastId:
            return None
        with self.con:
            self.con.row_factory = lite.Row
            cur =self.con.cursor() 
            cur.execute('SELECT * FROM log WHERE id BETWEEN %d AND %d'%(self.id,self.lastId))
            rows=cur.fetchall()  

        self.id=self.lastId
        return rows
