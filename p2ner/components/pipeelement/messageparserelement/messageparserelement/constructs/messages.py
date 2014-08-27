# -*- coding: utf-8 -*-
#   Copyright 2012 Loris Corazza, Sakis Christakidis
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from construct import *
from stream import StreamAdapter,  StreamStruct
from buffer import BufferAdapter,  BufferStruct, RequestAdapter
from peer import PeerAdapter,  PeerStruct
from swappeer import SwapPeerAdapter,SwapPeerStruct
from peerbuffer import PeerBufferStruct
from basemessage import BaseMessageAdapter, BaseMessageStruct

# Container( message = <PICKABLE msg>)
BaseMessage = Struct("basemessage",
        BaseMessageAdapter(BaseMessageStruct),
        )

# Container( streamid = <UInt16>)
SIDMessage = Struct("sidmessage",
        UBInt16("streamid"),
        )

# Container( streamid = <UInt16> swapid=<UInt16>)
SwapSIDMessage = Struct("swapsidmessage",
        UBInt16("streamid"),
        UBInt16("swapid"),
        )

# Container( streamid = <UInt16>, message = <PICKABLE msg>)
SIDBaseMessage = Struct("sidbasemessage",
        BaseMessageAdapter(BaseMessageStruct),
        UBInt16("streamid"),
        )

# Container( stream = <Stream obj>)
StreamMessage = Struct("streammessage",
        StreamAdapter(StreamStruct),
        )

# Container( stream = [<Stream obj>....])
MStreamMessage = Struct("mstreammessage",
        OptionalGreedyRange(StreamAdapter(StreamStruct)),
        )
# Container( streamid = <UInt16>, buffer = <Buffer obj>)
BufferMessage = Struct("buffermessage",
        UBInt16("streamid"),
        UBInt32("bw"),
        BufferAdapter(BufferStruct),
        Optional(RequestAdapter(MetaField("request",  lambda ctx: -(-ctx["buffer"].buffersize>>3)))),
        )

# Container( streamid = <UInt16>, peer = [Peer obj])
PeerListMessage = Struct("peerlistmessage",
        UBInt16("streamid"),
        OptionalGreedyRange(PeerAdapter(PeerStruct)),
        )

SPeerListMessage = Struct("speerlistmessage",
        UBInt16("streamid"),
        UBInt16("swapid"),
        OptionalGreedyRange(PeerAdapter(PeerStruct)),
        )

# Container( streamid = <UInt16>, peerbuffer = [Container(peer = <Peer obj>, buffer = <Buffer obj>)])
BufferListMessage = Struct("bufferlistmessage",
        UBInt16("streamid"),
        OptionalGreedyRange(PeerBufferStruct),
        )

RetransmitMessage=Struct("retransmitmessage",
        UBInt16("streamid"),
        BaseMessageAdapter(BaseMessageStruct),
        UBInt16('blockid'),
        )

RttMessage=Struct('rttmessage',
        UBInt16('rate'),
        UBInt16('sendrate'),
        BFloat64('rtt'),
        BFloat64('lrtt'),
        UBInt32('size'),
        UBInt16('blockId'),
        )

RegisterMessage=Struct("registermessage",
                       UBInt16("port"),
                       UBInt16('bw'),
                       Optional(PeerAdapter(PeerStruct)),
                       )

PeerMessage=Struct("peermessage",
                   PeerAdapter(PeerStruct),
                   )

OverlayMessage=Struct("overlaymessage",
                       UBInt16("streamid"),
                       UBInt16("port"),
                       UBInt16('bw'),
                       Optional(PeerAdapter(PeerStruct)),
                       )

LockMessage=Struct("lockmessage",
                   UBInt16('streamid'),
                   UBInt16('swapid'),
                   Flag('lock'),
                   )

SwapPeerListMessage = Struct("swappeerlistmessage",
        UBInt16("streamid"),
        UBInt16("swapid"),
        OptionalGreedyRange(SwapPeerAdapter(SwapPeerStruct)),
        )

SateliteMessage=Struct('satelitemessage',
        UBInt16('streamid'),
        UBInt16('swapid'),
        UBInt8('action'),
        PeerAdapter(PeerStruct),
        Optional(OverlayMessage)
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
             "swapsidmessage" : SwapSIDMessage,
             "sidbasemessage": SIDBaseMessage,
             "streammessage": StreamMessage,
             "mstreammessage": MStreamMessage,
             "buffermessage": BufferMessage,
             "peerlistmessage": PeerListMessage,
             "speerlistmessage": SPeerListMessage,
             "bufferlistmessage": BufferListMessage,
             "rawmessage": RawMessage,
             "retransmitmessage": RetransmitMessage,
             "rttmessage" : RttMessage,
             "registermessage" : RegisterMessage,
             "peermessage" :PeerMessage,
             "overlaymessage": OverlayMessage,
             "lockmessage": LockMessage,
             "swappeerlistmessage":SwapPeerListMessage,
             "satelitemessage":SateliteMessage
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

