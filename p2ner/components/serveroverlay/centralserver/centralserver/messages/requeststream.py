# -*- coding: utf-8 -*-

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
        self.overlay.addNeighbour(peer)

class RequestNeighboursMessage(ControlMessage):
    type = "sidmessage"
    code = MSG.SEND_IP_LIST
    ack = True
    
    def trigger(self, message):
        return self.stream.id == message.streamid

    def action(self, message, peer):
        self.log.debug('received request neighbour message from %s',peer)
        peerlist = self.overlay.getNeighbours(peer)
        PeerListMessage.send(self.stream.id, peerlist, peer, self.controlPipe)
        
