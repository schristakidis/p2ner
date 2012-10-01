# -*- coding: utf-8 -*

from p2ner.core.namespace import Namespace, initNS
from abc import abstractmethod

class UI(Namespace):

    @initNS
    def __init__(self, *args, **kwargs):
        self.initUI(*args, **kwargs)
    
    @abstractmethod
    def initUI(self, *args, **kwargs):
        pass
    """
    @abstractmethod
    def start(self):
        pass
    
    @abstractmethod
    def cleanUp(self):
        pass
    """