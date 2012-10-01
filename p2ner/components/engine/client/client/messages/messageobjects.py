# -*- coding: utf-8 -*-

from p2ner.base.Consts import MessageCodes as MSG
from construct import Container
from p2ner.base.ControlMessage import trap_sent, BaseControlMessage


class RequestStreamMessage(BaseControlMessage):
    type = "sidmessage"
    code = MSG.REQUEST_STREAM
    ack = True
    
    @classmethod
    def send(cls, sid, peer, out):
        c = Container(streamid = sid)
        return out.send(cls, c, peer).addErrback(trap_sent)

