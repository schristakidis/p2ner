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


from p2ner.abstract.pipeelement import PipeElement
from twisted.internet import reactor
from p2ner.base.Peer import Peer
from collections import deque
import time
from p2ner.core.statsFunctions import setValue

class BandwidthElement(PipeElement):

    def initElement(self, bw=200000, thres=3):
        self.log.info('BandwidthElement loaded')
        self.bw = bw
        self.que = deque()
        self.stuck = True
        self.thres = thres
        self.bwSet=False
        self.asked=False
        self.startTime=0
        self.idleTime=0
        self.lastIdleTime=0
        
    def send(self, res, msg, data, peer):
        if not self.startTime:
            self.startTime=time.time()
        for r in res:
            pack = (r, peer)
            self.que.append(pack)
        self.asked=False
        if self.stuck:
            if self.lastIdleTime:
                self.idleTime +=(time.time()-self.lastIdleTime)
                idle=self.idleTime/(time.time()-self.startTime)
                setValue(self,'netIdle',1000*idle)
            self.lastIdleTime=0
            self.stuck = False
            #self.log.debug('queue size %d',len(self.que))
            reactor.callLater(0, self.sendfromque)
        self.breakCall()
        return res
    
    def askdata(self):
        self.forwardprev("produceblock").callback("")
    
    def sendfromque(self):
        if len(self.que) == 0:
            self.lastIdleTime=time.time()
            self.stuck = True
            self.askdata()
            #self.log.error('asking for data queue empty')
            return
        res, peer = self.que.popleft()
        l=len(self.que)
        if len(self.que) <= self.thres: # and self.asked==False:
            self.askdata()
            self.asked=True
            #self.log.error('asking for data %d',l)
        #CHECK IF PEER BW IS SET
        #bw = getattr(peer, "bw", self.bw)
        bw=peer.bw
        #if bw==0:
        #    peer.bw=self.bw
         #   bw=self.bw
        #SET BW TO THE MIN
        #bw = min(bw, self.bw)
        if self.bwSet:
            bw=self.bw
            peer.bw=bw
            
        #print bw,peer.bw
        nextiter=1.0*len(res)/bw
        #print 'next iter:',nextiter
        reactor.callLater(nextiter, self.sendfromque)
        #print 'next:',nextiter
        #print 'total:',time.time()+nextiter
        self.forwardnext("send", None, None, peer).callback(res)
        
    #accpets KBytes/sec    
    def setBW(self, d, bw):
        self.bwSet=True
        self.bw=bw
        if self.bw>4*1024:
            self.bw=4*1024
            
        self.bw =self.bw*1024
        print 'setting bw to ',self.bw
        self.log.info('setting bw to %f',self.bw)
        return self.bw


