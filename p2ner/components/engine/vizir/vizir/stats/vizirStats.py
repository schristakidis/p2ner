
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

from p2ner.abstract.stats import Stats
from twisted.internet import task,reactor
from p2ner.util.utilities import get_user_data_dir
from twisted.enterprise import adbapi
from collections import deque
import os
import time
from collections import deque
from vizirStatsDB import DB as database
from p2ner.abstract.plugin import Plugin
from cPickle import loads
import time

class vizirStats(Plugin):
    def initPlugin(self, *args, **kwargs):
        if kwargs.has_key('statsDir'):
            dir=kwargs['statsDir']
        else:
            dir=get_user_data_dir()

        if not os.path.isdir(dir):
            os.mkdir(dir)

        self.peers={}
        self.systemStats=[]
        self.systemPeers=[]
        self.lpb = -1
        self.db=database(dir)
        self.subscribers={}
        self.loop = task.LoopingCall(self.updateDatabase)
        self.loop.start(2.0)
        self.waitingStats={}
        self.waitingStatsCount=0

    def getSystemPeers(self):
        try:
            sid=self.parent.getProducingId()
        except:
            return []
        if sid:
            sid=sid[0][1]
        else:
            return []

        return self.parent.getRunningPeerObjects(sid)

    def updateDatabase(self):
        self.clearStats()
        for s in self.systemStats:
            for p in list(set(self.systemPeers)):
                self.updateStat(p,s)
        for p,v in self.peers.items():
            stats=list(set(v['allstats']+self.systemStats))
            for s in stats:
                self.updateStat(p,s)

    def clearStats(self):
        self.systemPeers=self.getSystemPeers()
        for c in self.subscribers.keys():
            if not self.subscribers[c]['system']:
                for p in self.subscribers[c]['peers'].keys():
                    for s in self.subscribers[c]['peers'][p].keys():
                        self.subscribers[c]['peers'][p][s]=-1
            else:
                self.subscribers[c]['peers']={}
                for p in self.systemPeers:
                    self.subscribers[c]['peers'][p]={}
                    for s in self.subscribers[c]['stats']:
                        self.subscribers[c]['peers'][p][s]=-1



    def updateStat(self,peer,stat):
        d=self.db.getMaxValue(peer.getIP(),peer.getPort(),stat[0],stat[1],stat[2])
        d.addCallback(self.getStatValue,peer,stat)

    def getStatValue(self,maxV,peer,stat):
        maxV=maxV[0][0]
        if not maxV:
            maxV=0
        peer.getStatValue(stat,maxV,self.setStatValue)

    def setStatValue(self,value,peer,stat):
        value=loads(value)
        records=[]
        ip=peer.getIP()
        port=peer.getPort()

        for v in value:
            r=[ip,port,stat[0],stat[1],stat[2]]+v
            records.append(r)
        if records:
            self.db.update(records)
        self.checkUpdateSubscribers(stat,value,peer)

    def checkUpdateSubscribers(self,stat,value,peer):
        for k,v in self.subscribers.items():
            system=self.subscribers[k]['system']
            ret={}
            if peer in v['peers'].keys() and stat in v['peers'][peer].keys():
                v['peers'][peer][stat]=value
                ready=True
                for p in v['peers'].keys():
                    for s in v['peers'][p].keys():
                        if v['peers'][p][s]==-1:
                            ready=False
                            break
                        else:
                            if not system:
                                ret[s]=v['peers'][p][s]
                            else:
                                if s not in ret:
                                    ret[s]={}
                                ret[s][p]=v['peers'][p][s]
                if ready:
                    if not system:
                        v['func'](ret)
                    else:
                        self.constructSystemStats(ret,v['func'],v['x'])


    def subscribe(self,peers,stats,caller,func,x=None):
        if not peers:
            peers=[]
            system=True
            self.systemStats +=stats
        else:
            system=False
            for peer in peers:
                if peer not in self.peers:
                    self.peers[peer]={}
                    self.peers[peer]['allstats']=stats
                else:
                    self.peers[peer]['allstats']+=stats

        self.subscribers[caller]={}
        self.subscribers[caller]['func']=func
        self.subscribers[caller]['stats']=stats
        self.subscribers[caller]['x']=x
        self.subscribers[caller]['system']=system
        self.subscribers[caller]['peers']={}
        for p in peers:
            self.subscribers[caller]['peers'][p]={}
            for stat in stats:
                self.subscribers[caller]['peers'][p][stat]=-1


    def unsubscribe(self,caller):
        if not self.subscribers[caller]['system']:
            for p in self.subscribers[caller]['peers'].keys():
                for s in self.subscribers[caller]['peers'][p].keys():
                    self.peers[p]['allstats'].remove(s)
        else:
            for s in self.subscribers[caller]['stats']:
                self.systemStats.remove(s)

        del self.subscribers[caller]

    def getStats(self,peer,stats,func):
        self.waitingStats[self.waitingStatsCount]={}
        for s in stats:
            expr='WHERE %s < %s  AND ip IS "%s" AND port is %s AND comp IS "%s" AND sid IS %s AND name IS "%s" ORDER BY %s ASC'%(s[1],s[2],peer.getIP(),peer.getPort(),s[0][0],s[0][1],s[0][2],s[1])
            self.waitingStats[self.waitingStatsCount][(s[0][0],s[0][1],s[0][2])]=-1
            d=self.db.getRecords(expr)
            d.addCallback(self.returnStats,self.waitingStatsCount,func)
        self.waitingStatsCount+=1

    def returnStats(self,stat,count,func):
        for k,v in stat.items():
            self.waitingStats[count][k]=v

        ready=True
        for v in self.waitingStats[count].values():
            if v==-1:
                ready=False

        if ready:
            ret=self.waitingStats[count]
            del self.waitingStats[count]
            func(ret)



    def constructSystemStats(self,stats,func,x):
        if x=='time':
            i=2
        else:
            i=3

        dup={}
        allStats={}
        if x=='lpb':
            for s,peer in stats.items():
                dup[s]={}
                allStats[s]={}
                for p,val in peer.items():
                    dup[s][p]=[]
                    for v in val:
                        if v[i] not in dup[s][p]:
                            dup[s][p].append(v[i])
                            if v[i] not in allStats[s].keys():
                                allStats[s][v[i]]=[]
                            allStats[s][v[i]].append(v[0])

        if x=='time':
            for s,peer in stats.items():
                allStats[s]={}
                t = None
                for p,val in peer.items():
                    v=val[-1]
                    if not t:
                        t=v[i]
                        allStats[s][t]=[]
                    allStats[s][t].append(v[0])





        ret={}
        for s in allStats.keys():
            s10=(s[0],s[1],s[2]+'10')
            s50=(s[0],s[1],s[2]+'50')
            s90=(s[0],s[1],s[2]+'90')
            sav=(s[0],s[1],s[2]+'av')
            for suf in (s10,s50,s90,sav):
                ret[suf]=[]
            for i in sorted(allStats[s].keys()):
                v=sorted(allStats[s][i])
                ret[s10].append([v[int(0.1*len(v))],i,i,i])
                ret[s50].append([v[int(0.5*len(v))],i,i,i])
                ret[s90].append([v[int(0.9*len(v))],i,i,i])
                ret[sav].append([sum(v)/len(v),i,i,i])


        func(ret)



