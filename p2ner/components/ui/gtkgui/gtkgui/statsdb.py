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
    def __init__(self, name):
        self.dbpool=adbapi.ConnectionPool('sqlite3',name, check_same_thread=False)


    def _commitRecord(self,txn,args):
        for arg in args:
            txn.execute('INSERT INTO stat(comp, sid, name, value, x, time, lpb) VALUES(?,?,?,?,?,?,?)',arg)


    def getKeys(self):
        expr='SELECT DISTINCT comp,sid,name FROM stat'
        return self.dbpool.runQuery((expr))

    def getStats(self,stat):
        expr='SELECT * FROM stat WHERE comp IS "%s" AND sid IS %s AND name IS "%s" ORDER BY time ASC'%(stat[0],stat[1],stat[2])
        d=self._getRecords(expr)
        d.addCallback(self.updateId)
        return d

    def _getRecords(self,expr):
        return self.dbpool.runQuery((expr))

    def updateId(self,stats):
        ret={}
        for s in stats:
            key=(s[1],s[2],s[3])
            if (key) not in ret:
                ret[key]=[]
            ret[key].append([s[4],s[5],s[6],s[7]])
        return ret

    def stop(self):
        self.dbpool.close()
