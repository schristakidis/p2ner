# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage, trap_sent
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container

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
        for peer in message.peer:
            self['overlay'].addNeighbour(peer)
       
        
    @classmethod
    def send(cls, sid, peerlist, peer, out):
        return out.send(cls, Container(streamid=sid, peer=peerlist), peer).addErrback(trap_sent)
     
        
class RequestNeighbours(object):
    type = "sidmessage"
    code = MSG.SEND_IP_LIST
    ack = True

    @classmethod
    def send(cls, sid, peer, out):
        return out.send(cls, Container(streamid=sid), peer).addErrback(trap_sent)
     
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
        for peer in message.peer:
            if peer.ip==self.netChecker.externalIp:
                peer.useLocalIp=True
            self.producer=peer

       
    
    
    
