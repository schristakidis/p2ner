# -*- coding: utf-8 -*-

from abc import abstractmethod
from p2ner.core.namespace import Namespace, autoNS


class Message(Namespace):
    
    @autoNS
    def __init__(self, *args, **kwargs):
        self.initMessage(*args, **kwargs)
        
    @abstractmethod
    def initMessage(self, *args, **kwargs):
        pass

    @abstractmethod
    def trigger(self, message, peer):
        pass

    @abstractmethod
    def action(self, message):
        pass
