# -*- coding: utf-8 -*-

from p2ner.base.Consts import MessageCodes as MSG
from construct import Container
from p2ner.base.ControlMessage import BaseControlMessage, trap_sent

class ClientStartedMessage(BaseControlMessage):
    type = "basemessage"
    code = MSG.CLIENT_STARTED
    ack = True
    
    @classmethod
    def send(cls, port, server, out):
        msg = Container(message=port)
        return out.send(cls, msg, server).addErrback(trap_sent)

