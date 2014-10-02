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


from construct import Container
from p2ner.base.Consts import MessageCodes as MSG
from p2ner.base.ControlMessage import trap_sent, BaseControlMessage,probe_all,ControlMessage

class StreamMessage(BaseControlMessage):
    type = "streammessage"
    code = MSG.STREAM
    ack = True

    @classmethod
    def send(cls, stream, peer, out):
        return out.send(cls, Container(stream=stream), peer).addErrback(trap_sent)

class ReturnPeerStatus(BaseControlMessage):
    type = "overlaystatusmessage"
    code = MSG.GET_OVERLAY_STATUS
    ack = True

    @classmethod
    def send(cls, sid, superPeer, peer, out):
        return out.send(cls, Container(streamid=sid, superPeer=superPeer), peer).addErrback(trap_sent)


class PeerListMessage(BaseControlMessage):
    type = "peerlistoverlaymessage"
    code = MSG.SEND_IP_LIST2
    ack = True

    @classmethod
    def send(cls, sid,  soverlay, ioverlay, peerlist, peer, out):
        msg = Container(streamid = sid, superOverlay=soverlay, interOverlay=ioverlay , peer = peerlist)
        return out.send(cls, msg, peer).addErrback(trap_sent)


class PeerListProducerMessage(BaseControlMessage):
    type = "peerlistmessage"
    code = MSG.SEND_IP_LIST_PRODUCER
    ack = True

    @classmethod
    def send(cls, sid, peerlist, peer, out):
        #cls.log.debug('sending peerList message to %s',peer)
        msg = Container(streamid = sid, peer = peerlist)
        return out.send(cls, msg, peer).addErrback(trap_sent)

class PeerRemoveMessage(BaseControlMessage):
    type = "peerlistmessage"
    code = MSG.REMOVE_NEIGHBOURS
    ack = True

    @classmethod
    def send(cls, sid, peerlist, peer, out):
        #cls.log.debug('sending peerRemove message to %s',peer)
        msg = Container(streamid = sid, peer = peerlist)
        return out.send(cls, msg, peer).addErrback(trap_sent)

class PeerRemoveProducerMessage(PeerRemoveMessage):
    type = "peerlistmessage"
    code = MSG.REMOVE_NEIGHBOURS_PRODUCER
    ack = True

class SuggestNewPeerMessage(ControlMessage):
    type = "peerlistmessage"
    code = MSG.SUGGEST_NEW_PEER
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid:
            return False
        return True

    def action(self, message, peer):
        self.log.debug('received suggest new peer message from %s',peer)
        self.overlay.suggestNewPeer(peer,message.peer)

class SuggestMessage(BaseControlMessage):
    type = "peerlistmessage"
    code = MSG.SUGGEST
    ack = True

    @classmethod
    def send(cls, sid, peerlist, peer, out):
        return out.send(cls, Container(streamid=sid, peer=peerlist), peer).addErrback(trap_sent)
