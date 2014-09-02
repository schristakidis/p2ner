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
from twisted.internet import task,reactor
from p2ner.util.utilities import get_user_data_dir
from twisted.enterprise import adbapi
from collections import deque
import os
import time
from collections import deque
from db import DB as database

class DBStats(Stats):
    def initStats(self, *args, **kwargs):
        if kwargs.has_key('statsDir'):
            dir=kwargs['statsDir']
        else:
            dir=get_user_data_dir()

        if not os.path.isdir(dir):
            os.mkdir(dir)

        self.statkeys = {}
        self.lpb = -1
        self.startTime=None
        self.db=database(dir)
        self.subscribers={}
        self.loop = task.LoopingCall(self.updateDatabase)
        self.loop.start(2.0)


    def updateDatabase(self):
        subsStats={}
        stats=[]
        for comp in self.statkeys:
            for sid in self.statkeys[comp]:
                for key,v in self.statkeys[comp][sid].items():
                    subsStats[(comp,sid,key)]=[]
                    while v['values']:
                        temp=v['values'].popleft()
                        stats.append([comp,sid,key]+temp)
                        subsStats[(comp,sid,key)].append(temp)
        if stats:
            self.updateSubscribers(subsStats)
            self.db.update(stats)


    def setLPB(self, lpb):
        self.lpb = lpb


    def addKey(self, key, initValue=None,incrX=False):
        comp,key,sid=key
        if not self.startTime:
            self.startTime=int(100*time.time())
        if comp not in self.statkeys:
            self.statkeys[comp]={}
        if sid not in self.statkeys[comp]:
            self.statkeys[comp][sid]={}
        if key not in self.statkeys[comp][sid]:
            t=(int(100*time.time())-self.startTime)/100
            if incrX:
                x=0
            else:
                x=-1

            temp={}
            temp['values']=deque()
            temp['values'].append([initValue,x,t,self.lpb])
            if x!=-1:
                x +=1
            temp['x']=x
            temp['lastValue']=initValue
            self.statkeys[comp][sid][key]=temp

    def setKey(self, key, value):
        comp,key,sid=key
        try:
            x=self.statkeys[comp][sid][key]['x']
        except:
            raise KeyError('Key does not exists')

        t=(int(100*time.time())-self.startTime)/100.0
        self.statkeys[comp][sid][key]['values'].append([value,x,t,self.lpb])
        self.statkeys[comp][sid][key]['lastValue']=value
        if x!=-1:
            self.statkeys[comp][sid][key]['x']+=1

    def incrementKey(self, key, by=1):
        comp,key,sid=key
        try:
            x=self.statkeys[comp][sid][key]['x']
        except:
            raise KeyError('Key does not exists')

        lv=self.statkeys[comp][sid][key]['lastValue']
        t=(int(100*time.time())-self.startTime)/100.0
        self.statkeys[comp][sid][key]['values'].append([lv+by,x,t,self.lpb])
        if x!=-1:
            self.statkeys[comp][sid][key]['x']+=1
        self.statkeys[comp][sid][key]['lastValue']+=by

    def getKey(self, key):
        comp,key,sid=key
        try:
            return self.statkeys[comp][sid][key]
        except:
            raise KeyError('Key does not exists')

    def hasKey(self, key):
        comp,key,sid=key
        try:
            x=self.statkeys[comp][sid][key]['x']
            ret=True
        except:
            ret=False
        return ret


    def dumpKeys(self):
        ret = self.statkeys.copy()
        return ret

    def cleanUp(self):
        return

    def getAvailableStats(self):
        return self.dumpKeys()


    def subscribe(self,caller,func,keys):
        self.subscribers[caller]={}
        self.subscribers[caller]['func']=func
        self.subscribers[caller]['stats']=keys

    def unsubscribe(self,caller):
        del self.subscribers[caller]

    def getStats(self,stats):
        pass

    def updateSubscribers(self,stats):
        for v in self.subscribers.values():
            ret={}
            for k in v['stats']:
                ret[k]=stats[k]
            v['func'](ret)
