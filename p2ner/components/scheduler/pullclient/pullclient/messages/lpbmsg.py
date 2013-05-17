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

class LPBMessage(ControlMessage):
    type = "sidbasemessage"
    code = MSG.SERVER_LPB
    ack = False
    
    def trigger(self, message):
        #print "TRIGGER", message.streamid , self.stream.id
        return message.streamid == self.stream.id

    def action(self, message, peer):
        self.log.debug('received LPB message from %s',peer)
        #while self.buffer.lpb < message.message:
        #    self.scheduler.shift(norequests=True)
        self.buffer.lpb=message.message
        self.buffer.flpb=message.message
        if not self.loopingCall.running:
            #self.scheduler.start()
            self.streamComponent.start()
       

    @classmethod
    def send(cls, sid, lpb, peer, out):
        if not isinstance(peer, (list, tuple)):
            peer = [peer]
        out.send(cls, Container(streamid=sid, message=lpb, peer=peer))
       
