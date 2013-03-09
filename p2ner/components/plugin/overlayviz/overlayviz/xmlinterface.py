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
from cPickle import loads

class VizXMLInterface(Interface):
    def initInterface(self):
        pass
    
    def setId(self,id):
        self.id=id  
        
    def getNeighbours(self,func):
        self.func=func
        self.neighs={}
        for peer in self.parent.getRunningClients(self.id):
            ip=peer[0]
            port=peer[1]
            p=peer[7]
            
            self.neighs[(ip,port)]={}
            self.neighs[(ip,port)]['response']=False
            self.neighs[(ip,port)]['neighs']={}
            p.getNeighbours(self.id,ip,port,self.gotNeighs)
            
    def gotNeighs(self,neighs,ip,port):
        en=neighs[1]
        neighs = [loads(p) for p in neighs[0]]
        if self.neighs[(ip,port)]['response']:
            print 'already got the neighs from that peer'
            print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
        for p in neighs:
            try:
                p.plotRtt=sum(p.lastRtt)/len(p.lastRtt)
            except:
                print 'no rtt values ',p.lastRtt
                p.plotRtt=1
        self.neighs[(ip,port)]['response']=True
        self.neighs[(ip,port)]['neighs']=neighs
        self.neighs[(ip,port)]['energy']=en
        for p in self.neighs.values():
            if not p['response']:
                return
        self.constructNeighs()
        
    def constructNeighs(self):
        self.returnNeighs={}
        en=[]
        for k,v in self.neighs.items():
            self.returnNeighs[k]=[]
            en.append(v['energy'])
            for p in v['neighs']:
                self.returnNeighs[k].append(((p.getIP(),p.getPort()),p.plotRtt))
        
        self.func(self.returnNeighs,energy=en)