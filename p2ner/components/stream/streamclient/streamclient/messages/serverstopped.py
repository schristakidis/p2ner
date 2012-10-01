# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage
from p2ner.base.Consts import MessageCodes as MSG

class ServerStoppedMessage(ControlMessage):
    type = "sidbasemessage"
    code = MSG.SERVER_STOPPED
    ack = True
    
    def trigger(self, message):
        return message.streamid == self.stream.id

    def action(self, message, peer):
        self.streamComponent.stop()
            

