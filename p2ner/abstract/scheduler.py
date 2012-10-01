# -*- coding: utf-8 -*

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
