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


class AskInitNeighs(BaseControlMessage):
    type = "subsidmessage"
    code = MSG.ASK_INIT_NEIGHS_SUB
    ack = True

    @classmethod
    def send(cls, sid, superOverlay,interOverlay, peer, out):
        d=out.send(cls, Container(streamid = sid, superOverlay=superOverlay, interOverlay=interOverlay), peer)
        d.addErrback(trap_sent)
        return d

class PeerListMessage(ControlMessage):
    type = "subpeerlistmessage"
    code = MSG.SEND_IP_LIST_SUB
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerInitiatorsMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self, message, peer):
        self.log.debug('received peerList message from %s for %s',peer,str(message.peer))
        for p in message.peer:
            self.subOverlay.checkSendAddNeighbour(p,peer)

    @classmethod
    def send(cls, sid, peerlist, peer, out):
        return out.send(cls, Container(streamid=sid, peer=peerlist), peer).addErrback(trap_sent)




class AddNeighbourMessage(ControlMessage):
    type = "suboverlaymessage"
    code = MSG.ADD_NEIGH_SUB
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerMessage(message.superOverlay,message.interOverlay):
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
        self.log.debug('received add neigh message from %s',peer)
        print 'received neigh message from ',peer
        self.subOverlay.checkAcceptNeighbour(peer)

    @classmethod
    def send(cls, id,sOver,iOver,port,bw, inpeer, peer, out):
        msg = Container(streamid=id,superOverlay=sOver,interOverlay=iOver,port=int(port), bw=bw,peer=inpeer)
        d=out.send(cls, msg, peer)
        d.addErrback(trap_sent)
        return d

class ConfirmNeighbourMessage(ControlMessage):
    type = "subsidmessage"
    code = MSG.CONFIRM_NEIGH_SUB
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self, message, peer):
        self.subOverlay.addNeighbour(peer)

    @classmethod
    def send(cls, sid, sOver,iOver,peer, out):
        d=out.send(cls, Container(streamid = sid, superOverlay=sOver, interOverlay=iOver), peer)
        d.addErrback(trap_sent)
        return d



class SuggestNewPeerMessage(ControlMessage):
    type = "subpeerlistmessage"
    code = MSG.SUGGEST_NEW_PEER_SUB
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self, message, peer):
        self.log.debug('received suggest new peer message from %s',peer)
        self.subOverlay.suggestNewPeer(peer,message.peer)


    @classmethod
    def send(cls, sid,sover,iover, peerlist, peer, out, suc_func=None,err_func=None):
        return out.send(cls, Container(streamid=sid, superOverlay=sover, interOverlay=iover, peer=peerlist), peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func)

class SuggestMessage(ControlMessage):
    type = "subpeerlistmessage"
    code = MSG.SUGGEST_SUB
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self, message, peer):
        self.log.debug('received suggest  message from %s',peer)
        self.subOverlay.availableNewPeers(peer,message.peer)


    @classmethod
    def send(cls, sid,sover,iover, peerlist, peer, out):
        return out.send(cls, Container(streamid=sid, superOverlay=sover,interOverlay=iover, peer=peerlist), peer).addErrback(trap_sent)


class PingMessage(ControlMessage):
    type='basemessage'
    code=MSG.ADDNEIGH_RTT
    ack=True

    def trigger(self,message):
        return True

    def action(self,message,peer):
        return

    @classmethod
    def send(cls,  peer, out):
        out.send(cls,Container(message=None),peer).addErrback(trap_sent)

