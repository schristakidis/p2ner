# -*- coding: utf-8 -*

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
   
