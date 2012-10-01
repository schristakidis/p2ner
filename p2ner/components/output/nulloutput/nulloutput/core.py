# -*- coding: utf-8 -*

from p2ner.abstract.output import Output

class NullOutput(Output):
    
    def initOutput(self, *args, **kwargs):
        pass
    
    def write(self, data):
        pass
    
    def start(self):
        print 'Null Output starteddddddddddddd'
        
    def isRunning(self):
        return True
    
    def stop(self):
        pass