# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage, BaseControlMessage, trap_sent
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container


class StreamMessage(BaseControlMessage):
    type = "streammessage"
    code = MSG.PUBLISH_STREAM
    ack = True

    @classmethod
    def send(cls, stream, server, out):
        return out.send(cls, Container(stream=stream), server).addErrback(trap_sent)

class StreamIdMessage(ControlMessage):
    type = "sidbasemessage"
    code = MSG.STREAM_ID
    ack = True

    def initMessage(self, stream):
        self.stream = stream
        self.hash = stream.streamHash()
        
    def trigger(self, message):
        if message.message == self.hash:
            return True
        return False

    def action(self, message, peer):
        self.root.sidListeners.remove(self)
        self.stream.id = message.streamid
        self.root.newStream(self.stream)
        
