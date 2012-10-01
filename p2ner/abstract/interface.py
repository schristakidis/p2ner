# -*- coding: utf-8 -*

from p2ner.core.namespace import Namespace, initNS

class Interface(Namespace):
    
    @initNS
    def __init__(self, *args, **kwargs):
        self.stats={}
        self.initInterface(*args, **kwargs)
    
    def start(self):
        pass
    
    def setLiveProducer(self,id,setLive):
        pass
    
    def setLiveStream(self,id,live):
        pass
    
    def logRecord(self,record):
        pass
    
    def removeProducer(self,id):
        pass
    
    def displayError(self,error):
        pass
    
    def registerStat(self,stat):
         self.stats[stat]={}
         self.stats[stat]['count']=0
         self.stats[stat]['values']=[]
         
    def setStat(self,stat,v,t):
        self.stats[stat]['values'].append((v,t))
        self.stats[stat]['values']=self.stats[stat]['values'][-100:]
        self.stats[stat]['count'] +=1
        