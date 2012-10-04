# -*- coding: utf-8 -*
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


from p2ner.core.namespace import Namespace, initNS
from abc import abstractmethod

class Scheduler(Namespace):

    def sanityCheck(self, requirements):
        return
        for var in requirements:
            if var not in self.g:
                raise ValueError("%s is not a valid variable in current environment" % var)
    @initNS
    def __init__(self, *args, **kwargs):
        self.sanityCheck(["control", "controlPipe", "traffic", "trafficPipe", "overlay"])
        self.running = False
        self.initScheduler(*args, **kwargs)
    
    @abstractmethod
    def initScheduler(self):
        pass
    
    @abstractmethod
    def produceBlock(self):
        pass
        
    @abstractmethod
    def start(self):
        pass
    
    @abstractmethod
    def stop(self):
        self.purgeNS()
    
    @abstractmethod
    def isRunning(self):
        pass
    
    @property
    def bufferlist(self):
        sid = self.stream.id
        neighbours = self.overlay.getNeighbours()
        p = [n for n in neighbours if n.s.get(sid)]
        p = [n for n in p if n.s[sid].get("buffer")]
        ret = {}
        for peer in p:
            buf = peer.s[sid]["buffer"]
            buf.request = peer.s[sid].get("request", [])
            ret[buf] = peer
        return ret
