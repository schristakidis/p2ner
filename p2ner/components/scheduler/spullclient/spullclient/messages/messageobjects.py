# -*- coding: utf-8 -*-

from p2ner.base.Consts import MessageCodes as MSG
from construct import Container
from p2ner.base.ControlMessage import trap_sent, BaseControlMessage

class ClientStoppedMessage(BaseControlMessage):
    type = "sidmessage"
    code = MSG.CLIENT_STOPPED
    ack = True

    @classmethod
    def send(cls, sid, peer, out):
        return out.send(cls, Container(streamid=sid), peer).addErrback(trap_sent)
