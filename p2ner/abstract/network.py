# -*- coding: utf-8 -*

from p2ner.core.namespace import Namespace, initNS
from abc import abstractmethod

class Network(Namespace):

    @initNS
    def __init__(self, *args, **kwargs):
        self.initNetwork(*args, **kwargs)
    
    @abstractmethod
    def initNetwork(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def listen(self):
        pass
    
    @abstractmethod
    def send(self, data):
        return data
    
    @abstractmethod
    def cleanUp(self):
        pass
