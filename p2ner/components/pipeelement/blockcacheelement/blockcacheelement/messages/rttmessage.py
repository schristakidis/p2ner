# -*- coding: utf-8 -*-

from p2ner.base.Consts import MessageCodes as MSG
from construct import Container
from p2ner.base.ControlMessage import BaseControlMessage

class RTTMessage(BaseControlMessage):
    type = "rttmessage"
    code = MSG.RTT
    ack = False

    @classmethod
    def send(cls, rate,rtt, srate,lrtt,size,blockId,peer, out):
        return out.send(cls, Container(rate=rate,sendrate=srate, rtt=rtt,lrtt=lrtt,size=size,blockId=blockId), peer)