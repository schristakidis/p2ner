# -*- coding: utf-8 -*-

from construct import Container
from p2ner.base.Consts import MessageCodes as MSG
from p2ner.base.ControlMessage import trap_sent,BaseControlMessage

class StreamIdMessage(BaseControlMessage):
    type = "sidbasemessage"
    code = MSG.STREAM_ID
    ack = True

    @classmethod
    def send(cls, streamID, streamhash, peer, out):
        out.log.debug('sending streamid message to %s',peer)
        msg = Container(streamid = streamID, message = streamhash)
        return out.send(cls, msg, peer).addErrback(trap_sent)


class PeerListMessage(BaseControlMessage):
    type = "peerlistmessage"
    code = MSG.SEND_IP_LIST
    ack = True

    @classmethod
    def send(cls, streamID, peerlist, peer, out):
        out.log.debug('sending PeerList message to %s',peer)
        msg = Container(message = peerlist)
        return out.send(cls, msg, peer).addErrback(trap_sent)


class PeerRemoveMessage(BaseControlMessage):
    type = "peerlistmessage"
    code = MSG.REMOVE_NEIGHBOURS
    ack = True

    @classmethod
    def send(cls, streamID, peerlist, peer, out):
        out.log.debug('sending PeerRemove message to %s',peer)
        msg = Container(message = peerlist)
        return out.send(cls, msg, peer).addErrback(trap_sent)
        
class ContentsMessage(BaseControlMessage):
    type='mstreammessage'
    code=MSG.GET_CONTENTS
    ack=True
    
    @classmethod
    def send(cls,stream,peer,out):
        out.log.debug('sending contents message to %s',peer)
        return out.send(cls,Container(stream=stream),peer).addErrback(trap_sent)
