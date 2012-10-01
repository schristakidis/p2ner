# -*- coding: utf-8 -*-

from construct import *
from messageheader import MessageHeader
from stream import StreamAdapter,  StreamStruct
from buffer import BufferAdapter,  BufferStruct, RequestAdapter
from peer import PeerAdapter,  PeerStruct
from peerbuffer import PeerBufferStruct
from basemessage import BaseMessageAdapter, BaseMessageStruct

# Container(header = Container(ack = True|False, code = <UInt8>), message = <PICKABLE msg>)
BaseMessage = Struct("basemessage", 
        MessageHeader,
        BaseMessageAdapter(BaseMessageStruct),
        )

# Container(header = Container(ack = True|False, code = <UInt8>), streamid = <UInt16>)
SIDMessage = Struct("sidmessage",
        MessageHeader,
        UBInt16("streamid"),
        )

# Container(header = Container(ack = True|False, code = <UInt8>), streamid = <UInt16>, message = <PICKABLE msg>)
SIDBaseMessage = Struct("sidbasemessage",
        MessageHeader,
        BaseMessageAdapter(BaseMessageStruct),
        UBInt16("streamid"),
        )

# Container(header = Container(ack = True|False, code = <UInt8>), streamid = <UInt16>, stream = <Stream obj>)
StreamMessage = Struct("streammessage", 
        MessageHeader,
        StreamAdapter(StreamStruct), 
        )

MStreamMessage = Struct("mstreammessage", 
        MessageHeader,
        OptionalGreedyRepeater(StreamAdapter(StreamStruct)), 
        )
# Container(header = Container(ack = True|False, code = <UInt8>), streamid = <UInt16>, buffer = <Buffer obj>)
BufferMessage = Struct("buffermessage", 
        MessageHeader,
        UBInt16("streamid"), 
        BufferAdapter(BufferStruct), 
        Optional(RequestAdapter(MetaField("request",  lambda ctx: -(-ctx["buffer"].buffersize>>3)))),
        )

# Container(header = Container(ack = True|False, code = <UInt8>), streamid = <UInt16>, peer = [Peer obj])
PeerListMessage = Struct("peerlistmessage", 
        MessageHeader,
        UBInt16("streamid"), 
        OptionalGreedyRepeater(PeerAdapter(PeerStruct)), 
        )

# Container(header = Container(ack = True|False, code = <UInt8>), streamid = <UInt16>, peerbuffer = [Container(peer = <Peer obj>, buffer = <Buffer obj>)])
BufferListMessage = Struct("bufferlistmessage", 
        MessageHeader,
        UBInt16("streamid"), 
        OptionalGreedyRepeater(PeerBufferStruct), 
        )

class RawMessage(object):
    
    @staticmethod
    def parse(message):
        return message
    
    @staticmethod
    def build(message):
        return message

MSG_TYPES = {
             "basemessage" : BaseMessage,
             "sidmessage" : SIDMessage,
             "sidbasemessage": SIDBaseMessage,
             "streammessage": StreamMessage,
             "mstreammessage": MStreamMessage,
             "buffermessage": BufferMessage,
             "peerlistmessage": PeerListMessage,
             "bufferlistmessage": BufferListMessage,
             "rawmessage": RawMessage
             }


if __name__ == "__main__":
    from p2ner.base.Peer import Peer
    p = Peer("127.0.0.1", 50000, 50003)
    a = Container( message = [p], streamid = 1, header = Container(ack = True,code = 6))

    from p2ner.base.Buffer import Buffer
    b = BufferMessage.build( Container(header=Container(code=1, ack=False), streamid=22, buffer=Buffer(lpb=15), request=[3,6,8]))
    print len(b)
    print BufferMessage.parse(b)
    b = BufferMessage.build( Container(header=Container(code=1, ack=False), streamid=22, buffer=Buffer(lpb=15), request=None))
    print len(b)
    print BufferMessage.parse(b)
    exit(0)
    from p2ner.base.Stream import Stream
    s = '\x0b\x00\x00\x00\x00\x00\x0cpopipopi\x00\x00\x00\x00\x00\x00\x00\x9c?\x14\x07desc\x00\x08\x03'
    c =  StreamMessage.parse(s)
    print c
    print c.stream.classvars
    b = StreamMessage.build( Container(code = "STREAM",  streamid=0,  stream = Stream(None,  12,  
                                           "popipopi",  
                                           0,  
                                           39999,  
                                           20,  
                                           7,  
                                           "desc",  
                                           8,  
                                           3, )))
    print repr(b)
    assert b == s
    assert StreamMessage.build(c) == s
    
