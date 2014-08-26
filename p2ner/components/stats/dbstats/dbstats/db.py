# -*- coding: utf-8 -*-
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

from twisted.internet import task,reactor
from twisted.enterprise import adbapi
from collections import deque
import os
import time

class DB(object):
    def __init__(self, dir):
        dbname= os.path.join(dir,'stats.db')
        self.dbpool=adbapi.ConnectionPool('sqlite3',dbname, check_same_thread=False)
        d=self.deleteDB()
        d.addCallback(self.createDB)

    def deleteDB(self):
        return self.dbpool.runOperation('DROP TABLE IF EXISTS stat')

    def createDB(self,d):
        return self.dbpool.runOperation('CREATE TABLE stat(id INTEGER PRIMARY KEY AUTOINCREMENT, sid INTEGER, comp TEXT, name TEXT, value REAL, x REAL, time REAL, lpb INTEGER) ')

    def update(self,stats):
        d=self.dbpool.runInteraction(self._commitRecord,stats)

    def _commitRecord(self,txn,args):
        for arg in args:
            txn.execute('INSERT INTO stat(sid, comp, name, value, x, time, lpb) VALUES(?,?,?,?,?,?,?)',arg)

    def getRecords(self):
        d=self._getRecords()
        d.addCallback(self.updateId)
        return d

    def _getRecords(self):
        return self.dbpool.runQuery(('SELECT * FROM log WHERE id BETWEEN %d AND %d'%(self.id,self.lastId)))

    def updateId(self,records):
        dictR=[]
        self.id +=(len(records)+0)
        for r in records:
            dr={}
            dr['ip']=r[1]
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

    def stop(self):
        self.dbpool.disconnect()
