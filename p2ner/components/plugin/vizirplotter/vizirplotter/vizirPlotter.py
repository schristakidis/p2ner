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

from p2ner.abstract.plugin import Plugin
from twisted.internet import task
from cPickle import loads
from plot import PlotGui

class VizirPlotter(Plugin):
    def initPlugin(self,*args,**kwargs):
        self.showing=False
        self.stats={}
        self.loopingCall=task.LoopingCall(self.getStats)
        self.loopingCall.start(1)
        self.gui=None

    def toggle(self):
        if not self.stats:
            return
        if not self.gui:
            self.initGui()
        elif self.gui.showing:
            self.gui.ui_hide()
        else:
            self.gui.ui_show()

    def initGui(self):
        plots={}
        for k,v in self.stats.items():
            plots[k]=[str(i) for i in sorted(v.keys())]
        self.gui=PlotGui(plots)

    def getID(self):
        try:
            ids=self.root.getProducingId()
        except:
            return None
        if ids:
            return ids[0][1]
        else:
            return None

    def getPeers(self,sid):
        if not sid:
            return None
        peers={}
        for p in self.root.getRunningClients(sid):
            peers[(p[0],p[1])]={}
            peers[(p[0],p[1])]['peer']=p[7]
            peers[(p[0],p[1])]['stats']=False
        return peers


    def getStats(self):
        self.rawStats=[]
        sid=self.getID()
        self.peers=self.getPeers(sid)
        if not self.peers:
            return
        else:
            for k,v in self.peers.items():
                v['peer'].getStats(sid,k[0],k[1],self.newStats)

    def newStats(self,stats,ip,port):
        if stats==-1:
            self.peers.pop((ip,port))
        else:
            stats=loads(stats)
            self.rawStats.append(stats)
            self.peers[(ip,port)]['stats']=True

        self.checkFinish()

    def checkFinish(self):
        finish=True
        for v in self.peers.values():
            if not v['stats']:
                finish=False
                break

        if finish:
            self.prepareStats()

    def prepareStats(self):
        tempStats={}
        for l in self.rawStats:
            for p in l.values():
                for s,v in p.items():
                    if s not in self.stats:
                        self.stats[s]={}
                        self.stats[s]['10']=[]
                        self.stats[s]['50']=[]
                        self.stats[s]['90']=[]
                    if s not in tempStats:
                        tempStats[s]=[]
                    tempStats[s].append(v)
        self.writeStats(tempStats)

    def writeStats(self,stats):
        for k in self.stats.keys():
            if k not in stats:
                for v in ['10','50','90']:
                    self.stats[k][v].append(0)
            else:
                stats[k].sort()
                for v in ['10','50','90']:
                    self.stats[k][v].append(stats[k][int((int(v)/100.0)*len(stats[k]))])

        if self.gui and self.gui.showing:
            self.gui.updatePlots(self.stats)

    def destroy(self):
        if self.gui:
            self.gui.ui_destroy()



