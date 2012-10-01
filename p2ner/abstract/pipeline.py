# -*- coding: utf-8 -*

from p2ner.core.namespace import Namespace, initNS
from abc import abstractmethod
from weakref import ref
from random import random

class Pipeline(Namespace):

    @initNS
    def __init__(self, *args, **kwargs):
        self.producers = []
        self.initPipeline(*args, **kwargs)
        
    def producersCleanup(self):
        for p in self.producers:
            if not p():
                self.producers.remove(p)
        
    def registerProducer(self, producer):
        self.producers.append(ref(producer))
        
    def getRandomProducer(self):
        self.producersCleanup()
        running = [p for p in self.producers if p.running]
        if len(running):
            return random(running)
        return None

    def initPipeline(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def send(self, msg, content, peer):
        pass
    
    @abstractmethod
    def receive(self, data, (host, port)):
        pass
    
