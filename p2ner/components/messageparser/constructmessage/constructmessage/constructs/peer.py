# -*- coding: utf-8 -*-

from construct import *
from p2ner.base.Peer import Peer

class IpAddressAdapter(Adapter):
    def _encode(self, obj, context):
        return "".join(chr(int(b)) for b in obj.split("."))
    def _decode(self, obj, context):
        return ".".join(str(ord(b)) for b in obj)

class PeerAdapter(Adapter):
    def _encode(self,  obj,  ctx):
        return Container(IP = obj.ip,  port = obj.port,  dataport = obj.dataPort)
    def _decode(self,  obj,  ctx):
        return Peer(obj.IP,  obj.port,  obj.dataport)

PeerStruct = Struct( "peer", 
                   IpAddressAdapter(Bytes("IP",  4)),
                   UBInt16("port"), 
                   UBInt16("dataport"), 
                   )

if __name__ == "__main__":
    q = Container(IP = "127.0.0.1",  port = 10000,  dataport=20000)
    s = "\x7f\x00\x00\x01'\x10N "
    
    parsed = PeerAdapter(PeerStruct).parse(s)
    print parsed
    assert s == PeerAdapter(PeerStruct).build(parsed)
