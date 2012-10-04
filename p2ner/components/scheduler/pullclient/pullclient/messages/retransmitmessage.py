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

class RetransmitMessage(ControlMessage):
    type = "retransmitmessage"
    code = MSG.RETRANSMIT
    ack = False
    
    def trigger(self, message):
        #print "TRIGGER", message.streamid , self.stream.id
        return message.streamid == self.stream.id

    def action(self, message, peer):
        self.log.debug('received Retransmit message from %s for block %d and fragments %s',peer,message.blockid,str(message.message))
        self.scheduler.retransmit(message.blockid,message.message,peer)
       

    @classmethod
    def send(cls, sid, fragments,bid, peer, out):
        out.send(cls, Container(streamid=sid, message=fragments, blockid=bid),peer)
       
