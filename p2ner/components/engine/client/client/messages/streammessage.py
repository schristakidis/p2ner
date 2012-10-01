# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage, trap_sent
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container


class StreamMessage(ControlMessage):
    type = "streammessage"
    code = MSG.STREAM
    ack = True

    def trigger(self, message):
        return True

    def action(self, message, peer):
        if not self.root.getStream(message.stream):
            self.root.newStream(message.stream)
        
    @classmethod
    def send(self, stream, server, out):
        return self.out.send(Container(stream=stream)).addErrback(trap_sent)

