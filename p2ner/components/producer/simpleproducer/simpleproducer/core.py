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


from twisted.internet import task
from random import choice
from p2ner.abstract.scheduler import Scheduler
from p2ner.base.Buffer import Buffer
from messages.messageobjects import  ServerLPBMessage
from messages.retransmitmessage import RetransmitMessage
from p2ner.base.Peer import Peer
from p2ner.core.statsFunctions import setLPB, counter


class SimpleProducer(Scheduler):
    
    def registerMessages(self):
        self.messages = []
        self.messages.append(RetransmitMessage())
        
    
    def initScheduler(self):
        self.log.info('initing producer scheduler')
        self.registerMessages()
        self.loopingCall = task.LoopingCall(self.shift)
        self.blocksSec = self.stream.scheduler['blocksec'] 
        self.frequency = 1.0/self.stream.scheduler['blocksec']
        self.buffer = Buffer(buffersize=self.stream.scheduler['bufsize'],log=self.log)
        self.blockCache = {}
        
    def produceBlock(self):
        pass
    
    def sendLPB(self, peer):
        print peer
        self.log.debug('sending LPB message to %s',peer)
        ServerLPBMessage.send(self.stream.id, self.buffer.lpb, peer, self.controlPipe)
        
    def start(self):
        self.log.info('producer scheduler starts running')
        self.loopingCall.start(self.frequency)
        
    def stop(self):
        self.log.info('producer scheduler is stopping')
        try:
            self.loopingCall.stop()
        except:
            pass
        self.buffer = Buffer(buffersize=self.stream.scheduler['bufsize'],log=self.log)
        self.blockCache = {}
        
    
    def shift(self):
        from time import time
        #print "SHIFT: ", time()
        self.log.debug("SHIFT: %f",time())
        chunk = self.input.read()
        lpb = self.buffer.lpb
        #print self.buffer
        if chunk is None:
            self.log.warning('empty chunk')
            self.stop()
            return "EOF"
        
        if len(chunk) > 0:
            self.buffer.update(lpb)
            d = self.trafficPipe.call("inputblock", self, lpb, chunk)
            destination = self.overlay.getNeighbours()
            if len(destination)>0:
                for i in range(1):
                    #peer = choice(destination)
                    #ip='150.140.186.112'
                    #p=[p for p in destination if p.getIP()=='150.140.186.112']
                    #if p:
                    #   peer=p[0]
                    peer=sorted(destination, key=lambda p:p.reportedBW)[-1]
                    self.log.debug('sending block to %s %d %d',peer,self.buffer.lpb,len(chunk))
                    d.addCallback(self.sendblock, lpb, peer)
        
        outID,hit = self.buffer.shift()
        setLPB(self, self.buffer.lpb)
        self.log.debug('%s',self.buffer)
        outdata = self.trafficPipe.call("popblockdata", self, outID)
        outdata.addCallback(self.output.write)
        counter(self, "sent_block")
        
    def sendblock(self, r, bid, peer):
        return self.trafficPipe.call("sendblock", self, bid, peer)

    def isRunning(self):
        return self.loopingCall.running
    
    def retransmit(self,block,fragments,peer):
        print 'should retransmit to ',peer,block,fragments
        b={}
        b['blockid']=block
        b['fragments']=fragments
        self.trafficPipe.call('sendFragments',self,b,peer)
        
