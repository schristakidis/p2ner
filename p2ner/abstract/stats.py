# -*- coding: utf-8 -*
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

class Stats(Namespace):

    @initNS
    def __init__(self, *args, **kwargs):
        self.initStats(*args, **kwargs)
    
    @abstractmethod
    def initStats(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def cleanUp(self):
        pass
        
    @abstractmethod
    def setLPB(self, lpb):
        pass
    
    @abstractmethod
    def addKey(self, key, initValue=None):
        pass
        
    @abstractmethod
    def setKey(self, key, value):
        pass
    
    @abstractmethod
    def incrementKey(self, key, by=1):
        pass
        
    @abstractmethod
    def getKey(self, key):
        pass
        
    @abstractmethod
    def hasKey(self, key):
        pass
    
    @abstractmethod
    def dumpKeys(self):
        pass
