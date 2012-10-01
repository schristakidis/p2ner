# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage
from p2ner.base.Consts import MessageCodes as MSG
from twisted.internet import reactor

class PeerListMessage(ControlMessage):
    type = "peerlistmessage"
    code = MSG.SEND_IP_LIST_PRODUCER
    ack = True
    
    def trigger(self, message):
        return message.streamid == self.stream.id

    def action(self, message, peer):
        self.log.debug('received peerlist message in producer from  %s for peer %s',peer,message.peer)
        if  self.loopingCall.running:
            reactor.callLater(0.1, self.scheduler.sendLPB, message.peer)


