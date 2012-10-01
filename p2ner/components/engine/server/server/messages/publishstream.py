# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage, trap_sent
from p2ner.base.Consts import MessageCodes as MSG
from construct import *

class PublishStreamMessage(ControlMessage):
    type = "streammessage"
    code = MSG.PUBLISH_STREAM
    ack = True
    
    def trigger(self, message):
        #print "TRIGGER", message
        if message.stream.id != 0:
            return False
        return True

    def action(self, message, peer):
        stream = message.stream
        #print "RECEIVED STREAM:", stream
        producer = peer
        self.log.debug('received publish stream message from %s',peer)
        stream.id = self.root.generateStreamId(producer,stream.getServer())
        self.root.newStream(producer, stream)
        

    @classmethod
    def send(cls, stream, peer, out):
        cls.log.debug('sending publish stream message to %s',peer)
        return out.send(cls, Container(stream=stream), peer).addErrback(trap_sent)
