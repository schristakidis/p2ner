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
        if peer not in self.overlay.getNeighbours():
            print "NOT IN MY NEIGHBOUR LIST!", peer
        sid = self.stream.id
        if sid not in peer.s:
            peer.s[sid] = {}
        if "buffer" in peer.s[sid]:
            if peer.s[sid]["buffer"].lpb < self.buffer.lpb - self.buffer.buffersize:
                peer.s[sid] = {}
        if "buffer" in peer.s[sid]:
            if message.buffer.lpb > peer.s[sid]["buffer"].lpb:
                peer.s[sid]["buffer"] = message.buffer
                if "luck" in peer.s[sid]:
                    peer.s[sid]["buffer"].update(peer.s[sid]["luck"])
        else:
            peer.s[sid]["buffer"] = message.buffer
            peer.s[sid]["buffer"].flpb = self.buffer.lpb
            if "luck" in peer.s[sid]:
                peer.s[sid]["buffer"].update(peer.s[sid]["luck"])
        #self.log.debug('buffer:%s',str(message.buffer))
        if isinstance(message.request, list):
            peer.s[sid]["request"] = message.request
            if "luck" in peer.s[sid]:
                if peer.s[sid]["luck"] in peer.s[sid]["request"]:
                    peer.s[sid]["request"].remove(peer.s[sid]["luck"])
        if "luck" in peer.s[sid]:
            del peer.s[sid]["luck"]
            #self.log.debug('requests:%s',str(message.request))
        #print "RUNNING", self.scheduler.running
        if not self.scheduler.running:
            #"RESTART SCHEDULER"
            #self.log.debug('received buffer message from %s and should start scheduler',peer)
            self.scheduler.running = True
            self.scheduler.produceBlock()

    @classmethod
    def send(cls, sid, buffer, req, peer, out):
        if not req:
            req=None
        c = Container(streamid=sid, buffer=buffer, request=req)
        out.send(cls, c, peer)
        
