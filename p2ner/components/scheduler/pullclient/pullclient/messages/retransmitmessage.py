# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container

class RetransmitMessage(ControlMessage):
    type = "retransmitmessage"
    code = MSG.RETRANSMIT
    ack = False
    
    def trigger(self, message):
        #print "TRIGGER", message.streamid , self.stream.id
        return message.streamid == self.stream.id

    def action(self, message, peer):
        self.log.debug('received Retransmit message from %s for block %d and fragments %s',peer,message.blockid,str(message.message))
        self.scheduler.retransmit(message.blockid,message.message,peer)
       

    @classmethod
    def send(cls, sid, fragments,bid, peer, out):
        out.send(cls, Container(streamid=sid, message=fragments, blockid=bid),peer)
       
