# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage, BaseControlMessage, trap_sent
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container

class ServerStartedMessage(ControlMessage):
    type = "sidmessage"
    code = MSG.SERVER_STARTED
    ack = True
    
    def trigger(self, message):
        return message.streamid == self.stream.id

    def action(self, message, peer):
        if peer==self.server:
            self.log.debug('received serverStarted message from %s',peer)
            self.streamComponent.run()
        

    @classmethod
    def send(cls, sid, server, out):
        return out.send(cls, Container(streamid=sid), server).addErrback(trap_sent)
        
class ServerStoppedMessage(BaseControlMessage):
    type = "sidbasemessage"
    code = MSG.SERVER_STOPPED
    ack = True

    @classmethod
    def send(cls, sid, republish, server, out):
        return out.send(cls, Container(streamid=sid,message=republish), server).addErrback(trap_sent)
