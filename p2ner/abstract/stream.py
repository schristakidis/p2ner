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
from p2ner.core.components import loadComponent
from p2ner.base.Peer import Peer

defaultOutput = ("NullOutput", [], {})

class Stream(Namespace):

    def sanityCheck(self, requirements):
        for var in requirements:
            if var not in self.g:
                raise ValueError("%s is not a valid variable in current environment" % var)
    
    @initNS
    def __init__(self, *args, **kwargs):
        self.streamComponent=self
        if 'stream' in kwargs:
            self.stream=kwargs['stream']
        else:
            raise ValueError('you definetely need a stream')
        
        self.server=Peer(self.stream.server[0],self.stream.server[1])
        output = defaultOutput
        if "output" in kwargs:
            output = kwargs["output"]
        c, a, k = output
        self.log.debug('trying to load %s',c)
        output = loadComponent("output", c)
        self.output = output(_parent=self, *a, **k)
        if "input" in kwargs:
            c, a, k = kwargs["input"]
            self.log.debug('trying to load %s',c)
            input = loadComponent("input", c)
            self.input = input(_parent=self, *a, **k)

        self.initStream(*args, **kwargs)
    
    @abstractmethod
    def initStream(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def start(self):
        pass
  
    
    @abstractmethod
    def stop(self):
        pass
        """
        for c in [ "input", "output", "scheduler"]:
            if c in self:
                self[c].stop()
        """
        
    def getStreamID(self):
        return self.streamID
    
    def getStream(self):
        return self.stream
   
