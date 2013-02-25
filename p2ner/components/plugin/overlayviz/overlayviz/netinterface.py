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

from p2ner.abstract.interface import Interface
from messages.messages import GetNeighboursMessage,AskNeighboursMessage

class VizNetInterface(Interface):
    def initInterface(self):
        pass
    
    def getNeighbours(self,func):
        self.func=func
        self.neighs={}
        for peer in self.parent.getPeers():
            self.neighs[peer]={}
            self.neighs[peer]['response']=False
            self.neighs[peer]['neighs']={}
            self.neighs[peer]['msg']=GetNeighboursMessage(peer,self.gotNeighs)
            AskNeighboursMessage.send(peer,self.parent.stream.id,self.parent.controlPipe)
            
            
    def gotNeighs(self,peer,neighs):
        if self.neighs[peer]['response']:
            print 'already got the neighs from that peer'
            print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
        for p in neighs:
            p.plotRtt=sum(p.lastRtt)/len(p.lastRtt)
        self.neighs[peer]['response']=True
        self.neighs[peer]['neighs']=neighs
        self.neighs[peer]['msg']=None
        for p in self.neighs.values():
            if not p['response']:
                return
        self.constructNeighs()
        
    def constructNeighs(self):
        self.returnNeighs={}
        for k,v in self.neighs.items():
            peer=(k.getIP(),k.getPort())
            self.returnNeighs[peer]=[]
            for p in v['neighs']:
                self.returnNeighs[peer].append(((p.getIP(),p.getPort()),p.plotRtt))
        
        self.func(self.returnNeighs)
