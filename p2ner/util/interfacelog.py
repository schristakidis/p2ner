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

from p2ner.util.utilities import get_user_data_dir
from p2ner.abstract.interface import Interface
import os
from twisted.enterprise import adbapi
from twisted.internet import reactor
from collections import deque
import time

class DatabaseLog(Interface):
    def initInterface(self,server=False):
        self.que = deque()
        if server:
            self.defaultIp='server'
        else:
            self.defaultIp='peer'

        self.id=0
        self.lastId=0

        if server:
            self.start()
        else:
            self.getPort()

    def getPort(self):
        try:
            port=self.root.netChecker.controlPort
            self.start(port)
        except:
            reactor.callLater(1,self.getPort)

    def start(self,port='Server'):
        userdatadir = get_user_data_dir()
        if not os.path.isdir(userdatadir):
            os.mkdir(userdatadir)
        if not os.path.isdir(os.path.join(userdatadir, "log")):
            os.mkdir(os.path.join(userdatadir, "log"))
        n='p2ner'+str(port)+'.db'
        dbname= os.path.join(get_user_data_dir(), "log",n)
        print dbname

        self.dbpool=adbapi.ConnectionPool('sqlite3',dbname, check_same_thread=False)

        d=self.deleteDB()
        d.addCallback(self.createDB)
        d.addCallback(self.setReady)


    def deleteDB(self):
        return self.dbpool.runOperation('DROP TABLE IF EXISTS log')

    def createDB(self,d):
        return self.dbpool.runOperation('CREATE TABLE log(id INTEGER PRIMARY KEY AUTOINCREMENT, ip Text, port INTEGER, level TEXT, log TEXT, time TEXT, epoch REAL, msecs REAL,module TEXT, func TEXT, lineno INTEGER, msg TEXT) ')

    def setReady(self,d):
        reactor.callLater(1,self.commitRecords)

    def addRecord(self,record):
        self.lastId+=1
        try:
            ip=self.root.netChecker.externalIp
            port=self.root.netChecker.controlPort
        except:
            ip=self.defaultIp
            port=0
        args=(ip,port,record.levelname,record.name,time.time(),record.created,record.msecs,record.module,record.funcName,record.lineno,record.getMessage())
        self.que.append(args)

    def commitRecords(self):
        if len(self.que):
            args=[]
            while len(self.que):
                args.append(self.que.popleft())
            d=self.dbpool.runInteraction(self._commitRecord,args)
            d.addCallback(self.checkQue)
        else:
            reactor.callLater(1,self.commitRecords)

    def checkQue(self,d):
        reactor.callLater(1,self.commitRecords)

    def _commitRecord(self,txn,args):
        for arg in args:
            txn.execute('INSERT INTO log(ip,port,level,log,time,epoch,msecs,module,func,lineno,msg) VALUES(?,?,?,?,?,?,?,?,?,?,?)',arg)


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
        print 'should stop logger'
        self.dbpool.disconnect()
        #self.dbpool.runInteraction(self._stop)

    def _stop(self,txn):
        txn.close()
