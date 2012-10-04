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

class ClientStartedMessage(ControlMessage):
    type = "registermessage"
    code = MSG.CLIENT_STARTED
    ack = True
    
    def trigger(self, message):
        return True

    def action(self, message, peer):
        peer.dataPort=message.port
        peer.reportedBW=message.bw
        if message.peer:
            peer.lip=message.peer.ip
            peer.lport=message.peer.port
            peer.ldataPort=message.peer.dataPort
        
        print 'received client started message from ',peer,' bw:',message.bw
     
        self.log.debug('received client started message from %s',peer)
        if peer not in self.knownPeers:
            self.knownPeers.append(peer)        
            self.log.debug('appending %s to known peers',peer)



