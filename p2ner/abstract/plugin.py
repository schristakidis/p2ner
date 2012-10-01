# -*- coding: utf-8 -*

from p2ner.core.namespace import Namespace, initNS
from abc import abstractmethod

class Plugin(Namespace):

    @initNS
    def __init__(self, *args, **kwargs):
        self.initInput(*args, **kwargs)
    
    @abstractmethod
    def initPlugin(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def cleanUp(self):
        pass
