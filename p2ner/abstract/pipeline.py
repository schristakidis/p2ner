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
from weakref import ref
from random import random

class Pipeline(Namespace):

    @initNS
    def __init__(self, *args, **kwargs):
        self.producers = []
        self.initPipeline(*args, **kwargs)
        
    def producersCleanup(self):
        for p in self.producers:
            if not p():
                self.producers.remove(p)
        
    def registerProducer(self, producer):
        self.producers.append(ref(producer))
        
    def getRandomProducer(self):
        self.producersCleanup()
        running = [p for p in self.producers if p.running]
        if len(running):
            return random(running)
        return None

    def initPipeline(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def send(self, msg, content, peer):
        pass
    
    @abstractmethod
    def receive(self, data, (host, port)):
        pass
    
