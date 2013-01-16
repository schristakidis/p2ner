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

class SwapPeerAdapter(Adapter):
    def _encode(self,  obj,  ctx):
            rtt=-1
            if len(obj.lastRtt):
                rtt=sum(obj.lastRtt)/len(obj.lastRtt)
        
            if obj.lip:
                lip=obj.lip
                lport=obj.lport
                ldataport=obj.ldataPort
                hpunch=obj.hpunch
            else:
                lip='0.0.0.0'
                lport=0
                ldataport=0
                hpunch=False
 
           
            return Container(IP = obj.ip,  port = obj.port,  dataport = obj.dataPort, bw=obj.reportedBW, LIP = lip,  lport =lport,  ldataport = ldataport, hpunch=hpunch,rtt=rtt,swap=obj.participateSwap)

    def _decode(self,  obj,  ctx):
        p=Peer(obj.IP,  obj.port,  obj.dataport)
        p.reportedBW=obj.bw
        p.swapRtt=obj.rtt
        p.partnerParticipateSwap=obj.swap
        if obj.LIP=='0.0.0.0':
            p.lip=None
            p.lport=None
            p.ldataPort=None
            p.hpunch=False
        else:
            p.lip=obj.LIP
            p.lport=obj.lport
            p.ldataPort=obj.ldataport
            p.hpunch=obj.hpunch
        return p
    
SwapPeerStruct = Struct( "peer", 
                   IpAddressAdapter(Bytes("IP",  4)),
                   UBInt16("port"), 
                   UBInt16("dataport"),
                   UBInt16('bw'), 
                   IpAddressAdapter(Bytes("LIP",  4)),
                   UBInt16("lport"),
                   UBInt16("ldataport"),
                   Flag("hpunch"),
                   BFloat64("rtt"),
                   Flag("swap")
                   )
