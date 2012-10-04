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
