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
    type = "sidmessage"
    code = MSG.ASK_INIT_NEIGHS
    ack = True

    @classmethod
    def send(cls, sid, peer, out):
        d=out.send(cls, Container(streamid = sid), peer)
        d.addErrback(trap_sent)
        return d

class PeerListMessage(ControlMessage):
    type = "peerlistmessage"
    code = MSG.SEND_IP_LIST
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid:
            return False
        return True

    def action(self, message, peer):
        self.log.debug('received peerList message from %s for %s',peer,str(message.peer))
        for p in message.peer:
            self['overlay'].checkSendAddNeighbour(p,peer)

    @classmethod
    def send(cls, sid, peerlist, peer, out):
        return out.send(cls, Container(streamid=sid, peer=peerlist), peer).addErrback(trap_sent)



class PeerListPMessage(ControlMessage):
    type = "peerlistmessage"
    code = MSG.SEND_IP_LIST_PRODUCER
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid:
            return False
        return True

    def action(self, message, peer):
        self.log.debug('received peerList message from %s for %s',peer,str(message.peer))
        print 'receive peer list message for producer from ',peer,' for ',message.peer
        inpeer,port=self.root.checkNatPeer()
        bw=int(self.trafficPipe.callSimple('getBW')/1024)
        for p in message.peer:
            p.learnedFrom=peer
            print 'sending add producer message to ',p
            AddProducerMessage.send(self.stream.id,port,bw,inpeer,p,self['overlay'].addProducer,self['overlay'].failedProducer,self.root.controlPipe)




class AddNeighbourMessage(ControlMessage):
    type = "overlaymessage"
    code = MSG.ADD_NEIGH
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
        self.log.debug('received add neigh message from %s',peer)
        print 'received neigh message from ',peer
        self['overlay'].checkAcceptNeighbour(peer)

    @classmethod
    def send(cls, id,port,bw, inpeer, peer, out):
        msg = Container(streamid=id,port=int(port), bw=bw,peer=inpeer)
        d=out.send(cls, msg, peer)
        d.addErrback(trap_sent)
        return d

class ConfirmNeighbourMessage(ControlMessage):
    type = "sidmessage"
    code = MSG.CONFIRM_NEIGH
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid:
            return False
        return True

    def action(self, message, peer):
        self['overlay'].addNeighbour(peer)

    @classmethod
    def send(cls, sid, peer, out):
        d=out.send(cls, Container(streamid = sid), peer)
        d.addErrback(trap_sent)
        return d

class AddProducerMessage(BaseControlMessage):
    type = "overlaymessage"
    code = MSG.ADD_PRODUCER
    ack = True


    @classmethod
    def send(cls, id,port,bw, inpeer, peer,suc_func,err_func, out):
        msg = Container(streamid=id,port=port, bw=bw,peer=inpeer)
        d=out.send(cls, msg, peer)
        d.addErrback(probe_all,suc_func=suc_func,err_func=err_func)
        return d

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

class GetNeighsMessage(ControlMessage):
    type='basemessage'
    code=MSG.GET_NEIGHS
    ack=True

    def trigger(self,message):
        if message.message!=self.stream.id:
            return False
        return True

    def action(self,message,peer):
        self['overlay'].returnNeighs(peer)

class ReturnNeighsMessage(BaseControlMessage):
    type='swappeerlistmessage'
    code=MSG.RETURN_NEIGHS
    ack=True

    @classmethod
    def send(cls, sid, peerlist, peer, out):
        return out.send(cls, Container(streamid=sid, peer=peerlist), peer).addErrback(trap_sent)

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
        self['overlay'].suggestNewPeer(peer,message.peer)


    @classmethod
    def send(cls, sid, peerlist, peer, out, suc_func=None,err_func=None):
        return out.send(cls, Container(streamid=sid, peer=peerlist), peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func)

class SuggestMessage(ControlMessage):
    type = "peerlistmessage"
    code = MSG.SUGGEST
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid:
            return False
        return True

    def action(self, message, peer):
        self.log.debug('received suggest  message from %s',peer)
        self['overlay'].availableNewPeers(peer,message.peer)


    @classmethod
    def send(cls, sid, peerlist, peer, out):
        return out.send(cls, Container(streamid=sid, peer=peerlist), peer).addErrback(trap_sent)
