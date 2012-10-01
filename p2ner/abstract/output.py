# -*- coding: utf-8 -*

from p2ner.core.namespace import Namespace, initNS
from abc import abstractmethod

class Output(Namespace):

    @initNS
    def __init__(self, *args, **kwargs):
        self.initOutput(*args, **kwargs)
    
    @abstractmethod
    def initOutput(self, *args, **kwargs):
        pass
            
    @abstractmethod
    def write(self):
        pass
    
    @abstractmethod
    def isRunning(self):
        pass
    
    @abstractmethod
    def stop(self):
        self.purgeNS()
    
