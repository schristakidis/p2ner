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


from twisted.internet import reactor
from p2ner.abstract.pipeelement import PipeElement
from p2ner.base.Peer import Peer
import time
from messages.rttmessage import RTTMessage

class FlowControlElement(PipeElement):
    
    def initElement(self,bw=200000,inFactor=1.1,decFactor=0.8):
        self.inFactor=inFactor
        self.inDFactor=inFactor
        self.decFactor=decFactor
        self.bw=bw
        self.registerMessages()
        
        
    def registerMessages(self):
        self.messages = []
        self.messages.append(RTTMessage())

    def send(self, res, msg, data, peer):
         ret=res[0]
         self.updateBandwidth(res[1],peer)
         return ret
     
    def updateBandwidth(self,failed,peer):
        if not peer.bw:
             peer.bw=self.bw
             peer.lastTransmit=time.time()
             peer.prevFailed=False
             peer.reset=True
             peer.prevBw=0
             peer.thresBw=[]
             return
         
        if not failed:
             self.increaseBandwidth(peer)
        else:
             self.decreaseBandwidth(peer,failed)
             

    def increaseBandwidth(self,peer):
        return
        if time.time()-peer.lastTransmit>0.3 and not peer.prevFailed:
            peer.prevBw=peer.bw
            peer.bw=self.inFactor*peer.bw
            peer.lastTransmit=time.time()
            peer.prevFailed=False
            self.inFactor=self.inFactor
            #print 'increase bw for ',peer,' from ',peer.prevBw,' to ',peer.bw
        elif  peer.prevFailed and peer.reset:
            peer.reset=False
            reactor.callLater(3,self.resetFailed,peer)
    
    def decreaseBandwidth(self,peer,failed):
        return
        if not peer.prevFailed and peer.prevBw:
            peer.thresBw.append(peer.prevBw)
            peer.thresBw=peer.thresBw[-10:]
            peer.prevFailed=True
            #print 'first decrease  bw for ',peer,' from ',peer.prevBw,' to ',peer.bw
            #print peer.thresBw
            sum=0
            for b in peer.thresBw:
                sum +=b
            average=sum/len(peer.thresBw)
            print 'average:',sum/len(peer.thresBw)
            peer.bw=0.9*average
            peer.bwAverage=average
            self.inFactor=self.inDFactor
        else:
            peer.prevBw=peer.bw    
            peer.bw=peer.bw*self.decFactor
            #print 'decrease  bw for ',peer,' from ',peer.prevBw,' to ',peer.bw
        #self.breakCall()
            
    def resetFailed(self,peer):
        peer.prevFailed=False
        peer.reset=True
        print 'resetinggggggggg'
        
