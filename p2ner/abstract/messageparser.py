# -*- coding: utf-8 -*-

from p2ner.core.namespace import Namespace, initNS

from abc import abstractmethod

class MessageParser(Namespace):
    
    @initNS
    def __init__(self, *args, **kwargs):
        self.initMessageparser(*args, **kwargs)
    
    @abstractmethod
    def initMessageparser(self):
        pass
    
    @abstractmethod
    def encode(self, message):
        pass
        
    @abstractmethod
    def decode(self, message):
        pass