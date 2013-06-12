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


from p2ner.base.ControlMessage import ControlMessage
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container
from twisted.internet import reactor
from time import time

class BufferMessage(ControlMessage):
    type = "buffermessage"
    code = MSG.BUFFER
    ack = False
    
    def trigger(self, message):
        if message.streamid == self.stream.id:
            return True
        return False

    def action(self, message, peer):
        #print "===================================================="
        #print message
        #print "----------------------------------------------------"
        #TODO: LPB resynch if D(LPB) is wide
        #while self.buffer.lpb < message.buffer.lpb: 
        #    self.scheduler.shift()
        sid = self.stream.id
        if sid not in peer.s:
            peer.s[sid] = {}
        if "buffer" in peer.s[sid]:
            if message.buffer.lpb-1!=peer.s[sid]["buffer"].lpb:
                self.log.warning('problem in receiver buffer %s %d,%d',peer,message.buffer.lpb,peer.s[sid]['buffer'].lpb)
            if message.buffer.lpb > peer.s[sid]["buffer"].lpb:
                peer.s[sid]["buffer"] = message.buffer
        else:
            peer.s[sid]["buffer"] = message.buffer
            peer.s[sid]['lastRequest']=time()
        #self.log.debug('buffer:%s',str(message.buffer))
        #if isinstance(message.request, list):
        if message.buffer.lpb%self.scheduler.reqInterval ==0:
            if isinstance(message.request, list):
                peer.s[sid]["request"] = message.request
                check=True
            else:
                peer.s[sid]["request"]=[]
                check=False

            #self.log.debug('requests:%s',str(message.request))
            #print "RUNNING", self.scheduler.running
            peer.s[sid]['lastRequest']=time()
            #self.log.debug('received buffer message from %s %s %s',peer,peer.s[sid]['buffer'],peer.s[sid]["request"])
            if not self.scheduler.running and check:
                #self.log.warning('scheduler is not running')
                #"RESTART SCHEDULER"
                #self.log.debug('received buffer message from %s and should start scheduler',peer)
                #self.scheduler.running = True
                #maxlpb=max([p.s[sid]['buffer'].lpb for p in self.scheduler.bufferlist.values()])
                waitPeer=[p for p in self.scheduler.bufferlist.values() if time()-p.s[sid]['lastRequest']>self.scheduler.requestFrequency]
                #self.log.warning('waiting for %s',waitPeer)
                if not waitPeer:
                    #self.log.warning('starting scheduler')
                    reactor.callLater(0,self.scheduler.produceBlock)
     

    @classmethod
    def send(cls, sid, buffer, req, peer, out):
        if not req:
            req=None
        c = Container(streamid=sid, buffer=buffer, request=req)
        out.send(cls, c, peer)
        