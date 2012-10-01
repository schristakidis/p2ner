# -*- coding: utf-8 -*-

from p2ner.base.Consts import MessageCodes as MSG
from construct import Container
from p2ner.base.ControlMessage import BaseControlMessage,probe_ack
from p2ner.base.ControlMessage import trap_sent


class RequestStreamMessage(BaseControlMessage):
    type = "sidmessage"
    code = MSG.REQUEST_STREAM
    ack = True
    
    @classmethod
    def send(cls, sid, peer, out,func):
        d=out.send(cls, Container(streamid = sid), peer)
        d.addErrback(probe_ack,func)
        return d
    
        
class CheckContentsMessage(BaseControlMessage):
    type='basemessage'
    code=MSG.CHECK_CONTENTS
    ack=True
    
    @classmethod
    def send(cls,  server, out,func):
        d=out.send(cls, Container(message=None), server)
        d.addErrback(probe_ack,func)
        return d 
    
class StreamMessage(BaseControlMessage):
    type = "streammessage"
    code = MSG.PUBLISH_STREAM
    ack = True

    @classmethod
    def send(cls, stream, server, out, func):
        d=out.send(cls, Container(stream=stream), server)
        d.addErrback(probe_ack,func)
        return d
    
class ClientStartedMessage(BaseControlMessage):
    type = "registermessage"
    code = MSG.CLIENT_STARTED
    ack = True

    @classmethod
    def send(cls, port,bw, peer , server, out):
        d=out.send(cls, Container(port=port, bw=bw,peer=peer), server)
        d.addErrback(trap_sent)
        return d
