# -*- coding: utf-8 -*-
#   Copyright 2012 Loris Corazza, Sakis Christakidis
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


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
