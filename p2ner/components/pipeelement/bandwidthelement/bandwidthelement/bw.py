# -*- coding: utf-8 -*-

from p2ner.abstract.pipeelement import PipeElement
from twisted.internet import reactor
from p2ner.base.Peer import Peer
from collections import deque
import time

class BandwidthElement(PipeElement):

    def initElement(self, bw=200000, thres=3):
        self.log.info('BlockHeaderElement loaded')
        self.bw = bw
        self.que = deque()
        self.stuck = True
        self.thres = thres
        self.bwSet=False
    
    def send(self, res, msg, data, peer):
        for r in res:
            pack = (r, peer)
            self.que.append(pack)
        if self.stuck:
            self.stuck = False
            reactor.callLater(0, self.sendfromque)
        self.breakCall()
        return res
    
    def askdata(self):
        self.forwardprev("produceblock").callback("")
    
    def sendfromque(self):
        if len(self.que) == 0:
            self.stuck = True
            self.askdata()
            return
        res, peer = self.que.popleft()
        if len(self.que) <= self.thres:
            self.askdata()
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
        
    def setBW(self, d, bw):
        self.bwSet=True
        self.bw=bw
        if self.bw>2*1024:
            self.bw=2*1024
            
        self.bw =0.9 * self.bw*1024
        print 'setting bw to ',self.bw
        return self.bw
    
        
