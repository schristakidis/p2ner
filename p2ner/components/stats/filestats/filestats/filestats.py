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
import os

class FileStats(Stats):

    def initStats(self, *args, **kwargs):
        self.statkeys = {}
        self.fds = {}
        self.loop = task.LoopingCall(self.writeLog)
        self.loop.start(1.0)
        self.lpb = -1

    def cleanUp(self):
        self.clear()

    def setLPB(self, lpb):
        self.lpb = lpb
        
    def writeLog(self):
        for k in self.fds:
            self.fds[k].write(str(self.lpb))
            self.fds[k].write(" ")
            self.fds[k].write(str(self.statkeys[k]))
            self.fds[k].write("\n")
    
    def addKey(self, key, initValue=None):
        if not self.loop.running:
            return
        if key not in self.statkeys:
            self.statkeys[key] = initValue
            self.fds[key] = open(key + ".log", "w")
            self.fds[key].flush()
            os.fsync(self.fds[key].fileno())
            return
        raise KeyError('Key already exists: %s' % str(key))
        
    def closefds(self):
        for fd in self.fds:
            self.fds[fd].close()
    
    def setKey(self, key, value):
        if not self.loop.running:
            return
        if key not in self.statkeys:
            raise KeyError('Key does not exists')
        self.statkeys[key] = value
    
    def incrementKey(self, key, by=1):
        if key not in self.statkeys:
            raise KeyError('Key does not exists')
        self.statkeys[key] += by
        
    def getKey(self, key):
        if key not in self.statkeys:
            raise KeyError('Key does not exists')
        return self.statkeys[key]
        
    def hasKey(self, key):
        return key in self.statkeys

    def clear(self):
        self.loop.stop()
        self.closefds()
        self.statkeys = {}
        self.fds = {}

    def dumpKeys(self):
        ret = self.statkeys.copy()
        return ret
