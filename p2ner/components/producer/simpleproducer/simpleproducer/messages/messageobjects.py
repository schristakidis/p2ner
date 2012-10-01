# -*- coding: utf-8 -*-

from p2ner.base.Consts import MessageCodes as MSG
from construct import Container
from p2ner.base.ControlMessage import BaseControlMessage

class ServerLPBMessage(BaseControlMessage):
    type = "sidbasemessage"
    code = MSG.SERVER_LPB
    ack = False

    @classmethod
    def send(cls, sid, lpb, peer, out):
        return out.send(cls, Container(streamid=sid, message=lpb), peer)

