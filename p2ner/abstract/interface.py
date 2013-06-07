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
        
    def stop(self):
        try:
            self.logger.stop()
        except:
            pass