# -*- coding: utf-8 -*-

from p2ner.core.namespace import Namespace, initNS

from abc import abstractmethod

class Overlay(Namespace):

    def sanityCheck(self, requirements):
        return
        for var in requirements:
            if var not in self.g:
                raise ValueError("%s is not a valid variable in current environment" % var)
    
    @initNS
    def __init__(self, *args, **kwargs):
        self.initOverlay(*args, **kwargs)
    
    @abstractmethod
    def initOverlay(self):
        pass
    
    @abstractmethod
    def getNeighbours(self):
        pass
        
    @abstractmethod
    def addNeighbour(self):
        pass
    
    @abstractmethod
    def removeNeighbour(self):
        pass
    
    @abstractmethod
    def isNeighbour(self):
        pass
    
    @abstractmethod
    def stop(self):
        self.purgeNS()
