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
            for ov in range(3):
                self.neighs[(ip,port)][ov]={}
            p.getNeighbours(self.id,ip,port,self.gotNeighs)

    def gotNeighs(self,neighs,ip,port):
        if self.neighs[(ip,port)]['response']:
            print 'already got the neighs from that peer'
            print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'

        self.neighs[(ip,port)]['response']=True
        for ov,v in neighs.items():
            if v:
                n = [loads(p) for p in v['neighs']]
                for p in n:
                    try:
                        p.plotRtt=sum(p.lastRtt)/len(p.lastRtt)
                    except:
                        print 'no rtt values ',p.lastRtt
                        p.plotRtt=1

                self.neighs[(ip,port)][int(ov)]['neighs']=n
                self.neighs[(ip,port)][int(ov)]['energy']=neighs[ov]['energy']
                self.neighs[(ip,port)][int(ov)]['stats']=neighs[ov]['stats']
            else:
                self.neighs[(ip,port)][int(ov)]=None


        for p in self.neighs.values():
            if not p['response']:
                return
        self.constructNeighs()


    def constructNeighs(self):
        ret={}
        for ov in range(3):
            ret[ov]={}
            ret[ov]['neighs']={}
            ret[ov]['energy']=[]
            ret[ov]['stats']={}
            energy=[]
            for peer,v in self.neighs.items():
                if v[ov]:
                    ret[ov]['energy'].append(v[ov]['energy'])
                    ret[ov]['neighs'][peer]=[]
                    for p in v[ov]['neighs']:
                        ret[ov]['neighs'][peer].append(((p.getIP(),p.getPort()),p.plotRtt))
                    ret[ov]['stats'][peer]=v[ov]['stats']

        peers=self.neighs.keys()
        self.func(peers,ret)
