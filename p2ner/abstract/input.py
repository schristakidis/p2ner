# -*- coding: utf-8 -*

from p2ner.core.namespace import Namespace, initNS
from abc import abstractmethod

class Input(Namespace):

    @initNS
    def __init__(self, *args, **kwargs):
        self.initInput(*args, **kwargs)
    
    @abstractmethod
    def initInput(self, *args, **kwargs):
        pass
        
    @abstractmethod
    def read(self):
        pass
    
    @abstractmethod
    def isRunning(self):
        pass
    
    @abstractmethod    
    def stop(self):
        self.purgeNS()
