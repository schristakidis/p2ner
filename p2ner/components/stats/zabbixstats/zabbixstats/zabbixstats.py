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

from p2ner.abstract.stats import Stats
from twisted.internet import task
from p2ner.util.utilities import get_user_data_dir
from configobj import ConfigObj
from ZabbixSender.ZabbixSender import ZabbixSender
import time, os

class ZabbixStats(Stats):

    def initStats(self, *args, **kwargs):
        config = ConfigObj('/etc/zabbix/zabbix_agentd.conf')
        server = config.get('Server')
        self.host = config.get('Hostname').encode('utf-8')
        self.sender = ZabbixSender(server.encode('utf-8'))
        self.statkeys = {}
        self.loop = task.LoopingCall(self.sendStats)
        self.loop.start(1.0)
        self.lpb = -1

    def cleanUp(self):
        self.clear()

    def setLPB(self, lpb):
        self.lpb = lpb
        
    def sendStats(self):
        ret = self.sender.Send()
        print ret
        self.sender.ClearData()

    def addKey(self, key, initValue=0):
        if not self.loop.running:
            return
        if key not in self.statkeys:
            now = time.time()
            self.statkeys[key] = initValue
            k = "".join("p2ner.", key)
            self.sender.AddData(host = self.host, key = k.encode('utf-8'), value = initValue, clock = now)
            return
        raise KeyError('Key already exists: %s' % str(key))
        
    def setKey(self, key, value):
        if not self.loop.running:
            return
        if key not in self.statkeys:
            raise KeyError('Key does not exists')
        self.statkeys[key] = value
        now = time.time()
        k = "".join("p2ner.", key)
        self.sender.AddData(host = self.host, key = k.encode('utf-8'), value = value, clock = now)
    
    def incrementKey(self, key, by=1):
        if key not in self.statkeys:
            raise KeyError('Key does not exists')
        self.statkeys[key] += by
        now = time.time()
        k = "".join("p2ner.", key)
        self.sender.AddData(host = self.host, key = k.encode('utf-8'), value = self.statkeys[key], clock = now)

        
    def getKey(self, key):
        if key not in self.statkeys:
            raise KeyError('Key does not exists')
        return self.statkeys[key]
        
    def hasKey(self, key):
        return key in self.statkeys

    def clear(self):
        self.loop.stop()
        self.statkeys = {}
        self.sender.ClearData()

    def dumpKeys(self):
        ret = self.statkeys.copy()
        return ret

