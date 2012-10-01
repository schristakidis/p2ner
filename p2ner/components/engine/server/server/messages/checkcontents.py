# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage, trap_sent
from p2ner.base.Consts import MessageCodes as MSG
from construct import *

class CheckContentsMessage(ControlMessage):
    type = "basemessage"
    code = MSG.CHECK_CONTENTS
    ack = True
    
    def trigger(self, message):
        return True

    def action(self, message, peer):
        self.log.debug('received message check contents from %s',peer)
        self.root.sendContents(peer)
        

    @classmethod
    def send(cls, stream, peer, out):
        cls.log.debug('sending message check contents to %s',peer)
        return out.send(cls, Container(stream=stream), peer).addErrback(trap_sent)
