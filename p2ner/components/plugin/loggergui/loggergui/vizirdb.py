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
from twisted.enterprise import adbapi
from p2ner.util.testbed import LTOGIP,GTOLIP

class DatabaseLog(Interface):
    def initInterface(self,testbed):
        self.testbed=testbed
        userdatadir = get_user_data_dir()
        if not os.path.isdir(userdatadir):
            os.mkdir(userdatadir)
        if not os.path.isdir(os.path.join(userdatadir, "log")):
            os.mkdir(os.path.join(userdatadir, "log"))
        dbname= os.path.join(get_user_data_dir(), "log",'vizir.db')

        self.dbpool=adbapi.ConnectionPool('sqlite3',dbname,check_same_thread=False)
        self.id=0
        self.lastId=0
        d=self.deleteDB()
        d.addCallback(self.createDB)
        #d.addCallback(self.setReady)


    def deleteDB(self):
        return self.dbpool.runOperation('DROP TABLE IF EXISTS log')

    def createDB(self,d):
        return self.dbpool.runOperation('CREATE TABLE log(id INTEGER PRIMARY KEY AUTOINCREMENT, ip Text, port INTEGER, level TEXT, log TEXT, time TEXT, epoch REAL, msecs REAL,module TEXT, func TEXT, lineno INTEGER, msg TEXT) ')


    def addRecord(self,records):
        d=self.dbpool.runInteraction(self._commitRecords,records)
        return d

    def _commitRecords(self,txn,records):
        for r in records:
            args=(r['ip'],r['port'],r['level'],r['log'],r['time'],r['epoch'],r['msecs'],r['module'],r['func'],r['lineno'],r['msg'])
            txn.execute('INSERT INTO log(ip,port,level,log,time,epoch,msecs,module,func,lineno,msg) VALUES(?,?,?,?,?,?,?,?,?,?,?)',args)

    def getRecords(self):
        d=self._getRecords()
        d.addCallback(self.updateId)
        return d

    def _getRecords(self):
        return self.dbpool.runQuery('SELECT * FROM log ORDER by epoch')

    def updateId(self,records):
        dictR=[]
        self.id +=(len(records)+0)
        for r in records:
            dr={}
            if self.testbed:
                try:
                    ip=GTOLIP[r[1]]
                except:
                    ip=r[1]
            else:
                ip=r[1]

            dr['ip']=ip
            dr['port']=r[2]
            dr['level']=r[3]
            dr['log']=r[4]
            dr['time']=r[5]
            dr['epoch']=r[6]
            dr['msecs']=r[7]
            dr['module']=r[8]
            dr['func']=r[9]
            dr['lineno']=r[10]
            dr['msg']=r[11]
            dictR.append(dr)
        return dictR
