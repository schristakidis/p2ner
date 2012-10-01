# -*- coding: utf-8 -*

from p2ner.abstract.input import Input
import random

class RandomInput(Input):
    
    def initInput(self, *args, **kwargs):
        print self.stream
        blocksize = int(self.stream.bitRate/self.stream.blocksSec/8.0)
        b = ""              
        for i in xrange(blocksize):
            b+=chr(random.randint(0,255))
        self.block = b
    
    def read(self):
        return self.block
    
    def start(self):
        pass
        
    def isRunning(self):
        return True
    