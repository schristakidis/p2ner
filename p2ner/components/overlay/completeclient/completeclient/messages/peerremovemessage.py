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

from p2ner.base.ControlMessage import BaseControlMessage,ControlMessage, trap_sent
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container

class ClientStoppedMessage(ControlMessage):
    type = "subsidmessage"
    code = MSG.CLIENT_STOPPED_SUB
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self, message, peer):
        self.log.debug('received client stopped message from %s',peer)
        self.subOverlay.removeNeighbour(peer)

    @classmethod
    def send(cls, sid,sOver,iOver, peer, out):
        return out.send(cls, Container(streamid=sid , superOverlay=sOver, interOverlay=iOver), peer).addErrback(trap_sent)


class InformClientStoppedMessage(BaseControlMessage):
    type = "sidmessage"
    code = MSG.CLIENT_STOPPED
    ack = True


    @classmethod
    def send(cls, sid, peer, out):
        return out.send(cls, Container(streamid=sid), peer).addErrback(trap_sent)


class ClientDied(BaseControlMessage):
    type = "peerlistmessage"
    code = MSG.CLIENT_DIED
    ack = True


    @classmethod
    def send(cls, sid, peerlist, peer, out):
        return out.send(cls, Container(streamid=sid, peer=peerlist), peer).addErrback(trap_sent)
