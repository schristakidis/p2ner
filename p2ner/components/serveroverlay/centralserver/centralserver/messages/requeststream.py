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
from messageobjects import PeerListMessage

class RequestStreamMessage(ControlMessage):
    type = "sidmessage"
    code = MSG.REQUEST_STREAM
    ack = True
    
    def trigger(self, message):
        return self.stream.id == message.streamid

    def action(self, message, peer):
        self.log.debug('received request stream message from %s',peer)
        self.overlay.sendStream(peer)


class AskInitNeighsMessage(ControlMessage):
    type = "sidmessage"
    code = MSG.ASK_INIT_NEIGHS
    ack = True
    
    def trigger(self, message):
        return self.stream.id == message.streamid

    def action(self, message, peer):
        #self.log.debug('received request stream message from %s',peer)
        self.overlay.addNeighbour(peer)
