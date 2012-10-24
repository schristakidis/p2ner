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


from p2ner.base.ControlMessage import ControlMessage, trap_sent
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container

        
class AddProducerMessage(ControlMessage):   
    type = "overlaymessage"
    code = MSG.ADD_PRODUCER
    ack = True
    
    def trigger(self, message):
        if self.stream.id != message.streamid:
            return False
        return True    
       
    def action(self, message, peer):
        peer.dataPort=message.port
        peer.reportedBW=message.bw
        if message.peer:
            peer.lip=message.peer.ip
            peer.lport=message.peer.port
            peer.ldataPort=message.peer.dataPort
            peer.hpunch=message.peer.hpunch
        self.log.debug('received add neigh to producermessage from %s',peer)
        print 'received add neigh to producermessage from ',peer
        self['overlay'].addNeighbour(peer)       