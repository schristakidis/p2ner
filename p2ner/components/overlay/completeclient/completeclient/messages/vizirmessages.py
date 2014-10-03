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


from p2ner.base.ControlMessage import ControlMessage, trap_sent,probe_all,BaseControlMessage
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container


class GetNeighsMessage(ControlMessage):
    type='basemessage'
    code=MSG.GET_NEIGHS
    ack=True

    def trigger(self,message):
        if message.message!=self.stream.id:
            return False
        return True

    def action(self,message,peer):
        self.overlay.returnNeighs(peer)

class ReturnNeighsMessage(BaseControlMessage):
    type='swappeerlistmessage'
    code=MSG.RETURN_NEIGHS
    ack=True

    @classmethod
    def send(cls, sid, peerlist, peer, out):
        return out.send(cls, Container(streamid=sid, peer=peerlist), peer).addErrback(trap_sent)
