# -*- coding: utf-8 -*-

from construct import Container
from p2ner.base.Consts import MessageCodes as MSG
from p2ner.base.ControlMessage import trap_sent, BaseControlMessage,probe_rec

class StreamMessage(BaseControlMessage):
    type = "streammessage"
    code = MSG.STREAM
    ack = True

    @classmethod
    def send(cls, stream, peer, out,func):
        #cls.log.debug('sending stream message to %s',peer)
        return out.send(cls, Container(stream=stream), peer).addErrback(probe_rec,func)
        

class PeerListMessage(BaseControlMessage):
    type = "peerlistmessage"
    code = MSG.SEND_IP_LIST
    ack = True

    @classmethod
    def send(cls, sid, peerlist, peer, out):
        #cls.log.debug('sending peerList message to %s',peer)
        msg = Container(streamid = sid, peer = peerlist)
        return out.send(cls, msg, peer).addErrback(trap_sent)

class PeerListProducerMessage(PeerListMessage):
    type = "peerlistmessage"
    code = MSG.SEND_IP_LIST_PRODUCER
    ack = True
    

class PeerRemoveMessage(BaseControlMessage):
    type = "peerlistmessage"
    code = MSG.REMOVE_NEIGHBOURS
    ack = True

    @classmethod
    def send(cls, sid, peerlist, peer, out):
        #cls.log.debug('sending peerRemove message to %s',peer)
        msg = Container(streamid = sid, peer = peerlist)
        return out.send(cls, msg, peer).addErrback(trap_sent)

class PeerRemoveProducerMessage(PeerRemoveMessage):
    type = "peerlistmessage"
    code = MSG.REMOVE_NEIGHBOURS_PRODUCER
    ack = True